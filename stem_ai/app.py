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


_DEFAULT_REPO = "https://github.com/artic-network/fieldbioinformatics"


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
    warnings = [
        f"**{key.replace('_', ' ')}**: `{item['status']}`"
        for key, item in integrity.items()
        if item.get("status") != "PASS"
    ]
    warning_text = "\n".join(f"- {line}" for line in warnings) or "- No C1-C4 warning/fail status detected."
    return "\n".join(
        [
            "### Audit Snapshot",
            f"- **Final score:** `{score['final_score']} / 100`",
            f"- **Formal tier:** `{score['formal_tier']}`",
            f"- **Clinical adjacency:** `{classification['ca_severity']}`",
            f"- **Use scope:** {score['use_scope']}",
            "",
            "### Code Integrity Signals",
            warning_text,
        ]
    )


def _json_preview(result: dict) -> str:
    preview = {
        "schema_version": result["schema_version"],
        "stem_bio_ai_version": result["stem_ai_version"],
        "target": result["target"],
        "classification": result["classification"],
        "score": result["score"],
        "stage_2r_rubric": result.get("stage_2r_rubric", {}),
        "code_integrity": result.get("code_integrity", {}),
    }
    return json.dumps(preview, indent=2)


def run_demo(repo_url: str, level: int):
    repo_url = (repo_url or "").strip()
    if not repo_url:
        repo_url = _DEFAULT_REPO

    tmp_path = Path(tempfile.gettempdir()) / "stem_ai_demo" / uuid4().hex
    tmp_path.mkdir(parents=True, exist_ok=True)
    try:
        repo = _clone_github(repo_url, tmp_path)
        result = audit_repository(repo)
        mode, pages = _LEVEL_MAP[int(level)]
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


_LEVEL_CHOICES = [
    (1, "Level 1 — Brief  (1-page executive summary)"),
    (2, "Level 2 — Standard  (3-page: stage analysis + gap)"),
    (3, "Level 3 — Full  (5-page: deep integrity + remediation roadmap)"),
]

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
.boundary {
  border-left: 4px solid #d7a84a;
  padding: 10px 14px;
  background: #fff8e6;
  border-radius: 10px;
}
"""

with gr.Blocks(title="STEM BIO-AI Local Trust Audit", css=_CSS) as demo:
    gr.HTML(
        """
        <div class="hero">
          <h1>STEM BIO-AI</h1>
          <p>Contract-bound trust audit for open-source bio/medical AI repositories.
          Clone a public GitHub repo, inspect its visible evidence surface, and return
          JSON, Markdown, and PDF review artifacts.</p>
        </div>
        """
    )
    gr.Markdown(
        '<div class="boundary"><b>Boundary:</b> This is not clinical certification, '
        "regulatory clearance, scientific validation, or medical advice. It is a "
        "repository trust pre-screen based on observable artifacts.</div>"
    )
    with gr.Row():
        with gr.Column(scale=3):
            repo_input = gr.Textbox(
                label="Public GitHub repository URL",
                value=_DEFAULT_REPO,
                placeholder=_DEFAULT_REPO,
            )
        with gr.Column(scale=1):
            level_input = gr.Radio(
                choices=[1, 2, 3],
                value=1,
                label="Report Level",
                info="1=brief 1p, 2=standard 3p, 3=full 5p",
            )
    with gr.Row():
        run_button = gr.Button("Run STEM BIO-AI Audit", variant="primary", scale=2)
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
        with gr.Tab("Downloads"):
            gr.Markdown(
                "Artifact files are generated during the audit. "
                "The public demo shows the report and JSON preview in-browser; "
                "local CLI runs produce downloadable JSON/Markdown/PDF files."
            )
            with gr.Row():
                json_output = gr.Textbox(label="JSON artifact", interactive=False)
                pdf_output = gr.Textbox(label="PDF artifact", interactive=False)
    click_kwargs = {
        "fn": run_demo,
        "inputs": [repo_input, level_input],
        "outputs": [score_output, snapshot_output, report_output, json_preview, json_output, pdf_output],
        "api_name": False,
        "queue": True,
    }
    if _gradio_major() < 6:
        click_kwargs["show_api"] = False
    else:
        click_kwargs["api_visibility"] = "undocumented"

    run_button.click(
        **click_kwargs,
    )
    clear_button.add(
        [repo_input, score_output, snapshot_output, report_output, json_preview, json_output, pdf_output]
    )


def launch_demo() -> None:
    """Launch the Space UI without exposing Gradio's generated API schema."""
    # Gradio 4.44 can crash while deriving client schemas for some components.
    # This Space is an interactive demo, not a public API, so skip API metadata.
    demo.get_api_info = lambda: {}

    launch_kwargs = {
        "server_name": "0.0.0.0",
        "server_port": 7860,
        "share": True,
    }
    if _gradio_major() < 6:
        launch_kwargs["show_api"] = False
    demo.queue(api_open=False).launch(**launch_kwargs)
