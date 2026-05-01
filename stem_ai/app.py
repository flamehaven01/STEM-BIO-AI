from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4
import json

from .cli import _LEVEL_MAP
from .render import render_markdown, write_outputs
from .scanner import audit_repository

try:
    import gradio as gr
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "Gradio failed to import. Install demo dependencies with "
        "`pip install -r requirements.txt` or `pip install -e .[demo]`. "
        f"Original error: {exc}"
    ) from exc


_DEFAULT_REPO = "https://github.com/flamehaven01/STEM-BIO-AI"
_PLACEHOLDER_REPO = "https://github.com/<owner>/<bio-medical-ai-repo>"


def _gradio_major() -> int:
    try:
        return int(str(gr.__version__).split(".", 1)[0])
    except (AttributeError, TypeError, ValueError):
        return 4


def _clone_github(url: str, destination: Path) -> Path:
    if not url.startswith("https://github.com/"):
        raise ValueError("Only public https://github.com/ URLs are supported in the demo.")
    target = destination / "repo"
    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(target)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git clone failed")
    return target


def _finding_cards(result: dict) -> str:
    score = result["score"]
    classification = result["classification"]
    integrity = result["code_integrity"]
    s3 = result.get("stage_3_rubric", {})

    # Stage scores
    stage_lines = [
        "| Stage | Score |",
        "|-------|------:|",
        f"| Stage 1 README Evidence | `{score['stage_1_readme_intent']} / 100` |",
        f"| Stage 2R Repo Consistency | `{score['stage_2_repo_local_consistency']} / 100` |",
        f"| Stage 3 Code/Bio Responsibility | `{score['stage_3_code_bio']} / 100` |",
    ]

    # Stage 3 3-tier detail
    t3_score = s3.get("T3_changelog_release_hygiene", {}).get("score", 0)
    b1_score = s3.get("B1_data_provenance_controls", {}).get("score", 0)
    b2_score = s3.get("B2_bias_limitations", {}).get("score", 0)

    # Replication lane
    rep_score = result.get("replication_score", "n/a")
    rep_tier = result.get("replication_tier", "n/a")

    # Code integrity
    warnings = [
        f"**{key.replace('_', ' ')}**: `{item['status']}`"
        for key, item in integrity.items()
        if item.get("status") != "PASS"
    ]
    warning_text = "\n".join(f"- {line}" for line in warnings) or "- No C1-C4 warning/fail status detected."

    # Notable signals
    risks = result.get("notable_risks", [])
    positives = result.get("notable_positive_evidence", [])
    risk_text = "\n".join(f"- {r}" for r in risks[:4]) or "- None detected."
    pos_text = "\n".join(f"- {p}" for p in positives[:4]) or "- None detected."

    return "\n".join(
        [
            "### Audit Snapshot",
            f"- **Final score:** `{score['final_score']} / 100`",
            f"- **Formal tier:** `{score['formal_tier']}`",
            f"- **Clinical adjacency:** `{classification['ca_severity']}`",
            f"- **Use scope:** {score['use_scope']}",
            "",
            "### Stage Scores",
            *stage_lines,
            "",
            "### Stage 3 Detail",
            f"- T3 Changelog hygiene: `{t3_score}` &nbsp; B1 Data provenance: `{b1_score}` &nbsp; B2 Bias measurement: `{b2_score}`",
            "",
            "### Replication Lane (Stage 4)",
            f"- Score: `{rep_score}` &nbsp; Tier: `{rep_tier}`",
            "",
            "### Code Integrity",
            warning_text,
            "",
            "### Notable Risks",
            risk_text,
            "",
            "### Positive Evidence",
            pos_text,
        ]
    )


def _json_preview(result: dict) -> str:
    preview = {
        "schema_version": result["schema_version"],
        "stem_ai_version": result["stem_ai_version"],
        "target": result["target"],
        "classification": result["classification"],
        "score": result["score"],
        "replication_score": result.get("replication_score"),
        "replication_tier": result.get("replication_tier"),
        "stage_1_rubric": result.get("stage_1_rubric", {}),
        "stage_2r_rubric": result.get("stage_2r_rubric", {}),
        "stage_3_rubric": result.get("stage_3_rubric", {}),
        "stage_4_rubric": result.get("stage_4_rubric", {}),
        "code_integrity": result.get("code_integrity", {}),
        "notable_positive_evidence": result.get("notable_positive_evidence", []),
        "notable_risks": result.get("notable_risks", []),
    }
    return json.dumps(preview, indent=2)


def run_demo(repo_url: str, level: int):
    repo_url = (repo_url or "").strip()
    try:
        level_int = int(level)
    except (TypeError, ValueError):
        level_int = 1
    if level_int not in _LEVEL_MAP:
        level_int = 1
    if not repo_url:
        return (
            "Waiting for repository URL",
            "### Input required\nPaste a public GitHub URL for a bio/medical AI repository.",
            "No report generated.",
            json.dumps({"status": "input_required", "example": _DEFAULT_REPO}, indent=2),
            "No JSON artifact generated.",
            "No PDF artifact generated.",
        )

    tmp_path = Path(tempfile.gettempdir()) / "stem_ai_demo" / uuid4().hex
    tmp_path.mkdir(parents=True, exist_ok=True)
    try:
        repo = _clone_github(repo_url, tmp_path)
        result = audit_repository(repo)
        mode, pages = _LEVEL_MAP[level_int]
        output_dir = tmp_path / "out"
        files = write_outputs(result, output_dir, mode, pages, "all")
        report = render_markdown(result, mode, pages)
        json_file = next(p for p in files if p.name.endswith("_experiment_results.json"))
        pdf_file = next(p for p in files if p.suffix == ".pdf")
        return (
            f"{result['score']['final_score']} / 100  ({result['score']['formal_tier']})",
            _finding_cards(result),
            report,
            _json_preview(result),
            f"Generated JSON artifact: `{json_file.name}`",
            f"Generated PDF artifact: `{pdf_file.name}`",
        )
    except Exception as exc:
        return (
            "Audit failed",
            f"### Error\n`{type(exc).__name__}: {exc}`",
            "No report generated.",
            json.dumps({"error": str(exc), "error_type": type(exc).__name__}, indent=2),
            "No JSON artifact generated.",
            "No PDF artifact generated.",
        )


_CSS = """
.hero {
  padding: 28px;
  border-radius: 22px;
  background: linear-gradient(135deg, #10233f 0%, #17616f 52%, #d7a84a 100%);
  color: white;
  margin-bottom: 18px;
}
.hero h1 { font-size: 42px; line-height: 1.05; margin: 0 0 10px; }
.hero p { font-size: 17px; max-width: 820px; margin: 0; }
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin: 20px 0;
}
.info-card {
  border: 1px solid #dde6ef;
  border-radius: 14px;
  padding: 16px;
  background: #ffffff;
  color: #111827;
  min-height: 132px;
  box-shadow: 0 8px 24px rgba(16, 35, 63, 0.08);
}
.info-card b {
  color: #0f172a;
  display: block;
  font-size: 15px;
  font-weight: 800;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}
.info-card span {
  color: #1f2937;
  font-size: 14px;
  line-height: 1.45;
}
.info-card .cli-command {
  background: #dbeafe;
  border: 1px solid #93c5fd;
  border-radius: 7px;
  color: #0f172a;
  display: inline-block;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
  font-weight: 800;
  margin: 3px 0;
  padding: 3px 7px;
}
"""

with gr.Blocks(title="STEM BIO-AI — Evidence Scanner v1.5.5") as demo:
    gr.HTML(
        """
        <div class="hero">
          <h1>STEM BIO-AI <span style="font-size:22px;font-weight:400;opacity:0.75">v1.5.5</span></h1>
          <p>Deterministic evidence-surface scanner for bio/medical AI repositories.
          No LLM. No API key. No model runtime.
          Clone a public GitHub repo, inspect its observable evidence surface (README, docs, CI,
          tests, changelogs, dependency manifests), and return a scored T0–T4 triage tier with
          full JSON, Markdown, and PDF artifacts.</p>
        </div>
        """
    )
    gr.HTML(
        """
        <div class="info-grid">
          <div class="info-card"><b>No API key required</b>
          <span>Clones a public GitHub repository and runs a fully deterministic local scanner.
          Does not call OpenAI, Anthropic, GitHub API, or any external service.</span></div>

          <div class="info-card"><b>What STEM scans</b>
          <span>Stage 1: README hype/responsibility signals (H1–H6 penalties, R1–R5 credits).
          Stage 2R: repo-local consistency. Stage 3: CI, domain tests, changelog hygiene,
          data provenance, bias measurement. Stage 4: replication evidence lane.</span></div>

          <div class="info-card"><b>Triage tiers</b>
          <span>T0 Rejected · T1 Quarantine · T2 Caution · T3 Supervised ·
          T4 Candidate. Clinical-adjacent repos without a disclaimer are hard-capped at T2.
          A T4 score is not a clinical safety rating.</span></div>

          <div class="info-card"><b>Local CLI</b>
          <span>Use <code class="cli-command">stem &lt;folder&gt; --level 3 --format all --explain</code>
          locally to generate downloadable JSON, Markdown, PDF, and proof-trace artifacts.</span></div>
        </div>
        """
    )
    gr.Markdown(
        "Paste a public bio/medical AI repository URL below. The demo works best on repositories "
        "with README/docs/tests/dependency files. Private repositories should be audited locally."
    )
    with gr.Row():
        with gr.Column(scale=3):
            repo_input = gr.Textbox(
                label="Public GitHub repository URL",
                value="",
                placeholder=_PLACEHOLDER_REPO,
                info=(
                    "Paste a public bio/medical AI repository URL. "
                    f"Safe demo repository: {_DEFAULT_REPO}"
                ),
            )
        with gr.Column(scale=1):
            level_input = gr.Radio(
                choices=[
                    ("Brief - 1 page", 1),
                    ("Standard - 3 pages", 2),
                    ("Full - 5 pages", 3),
                ],
                value=1,
                label="Report Level",
                info="Brief, Standard, or Full report depth.",
            )
    with gr.Row():
        run_button = gr.Button("Run live GitHub audit", variant="primary", scale=2)
        clear_button = gr.ClearButton(value="Clear", scale=1)
    score_output = gr.Textbox(label="Final Score", interactive=False)
    snapshot_output = gr.Markdown(label="Audit Snapshot")
    with gr.Tabs():
        with gr.Tab("Report"):
            report_output = gr.Markdown(label="Markdown report")
        with gr.Tab("JSON Preview"):
            json_preview = gr.Code(
                label="Machine-readable evidence object",
                language="json",
                interactive=False,
                lines=24,
            )
        with gr.Tab("Local CLI Artifacts"):
            gr.Markdown(
                "This public Space shows report and JSON previews in-browser. "
                "For actual downloadable JSON/Markdown/PDF artifacts, run the local CLI."
            )
            with gr.Row():
                json_output = gr.Textbox(label="JSON artifact", interactive=False)
                pdf_output = gr.Textbox(label="PDF artifact", interactive=False)
    click_kwargs = {
        "fn": run_demo,
        "inputs": [repo_input, level_input],
        "outputs": [score_output, snapshot_output, report_output, json_preview, json_output, pdf_output],
        "queue": True,
    }

    run_button.click(
        **click_kwargs,
    )
    clear_button.add(
        [repo_input, score_output, snapshot_output, report_output, json_preview, json_output, pdf_output]
    )


def launch_demo() -> None:
    """Launch the Space UI."""
    demo.queue().launch(css=_CSS, server_name="0.0.0.0", server_port=7860)
