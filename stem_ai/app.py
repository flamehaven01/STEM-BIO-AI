from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

from .cli import _LEVEL_MAP
from .render import render_markdown, write_outputs
from .scanner import audit_repository

try:
    import gradio as gr
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install demo dependencies with: pip install -e .[demo]") from exc


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


def run_demo(repo_url: str, level: int):
    tmp_path = Path(tempfile.gettempdir()) / "stem_ai_demo" / uuid4().hex
    tmp_path.mkdir(parents=True, exist_ok=True)
    repo = _clone_github(repo_url.strip(), tmp_path)
    result = audit_repository(repo)
    mode, pages = _LEVEL_MAP[level]
    output_dir = tmp_path / "out"
    files = write_outputs(result, output_dir, mode, pages, "all")
    report = render_markdown(result, mode, pages)
    json_file = next(p for p in files if p.name.endswith("_experiment_results.json"))
    pdf_file  = next(p for p in files if p.suffix == ".pdf")
    return (
        f"{result['score']['final_score']} / 100  ({result['score']['formal_tier']})",
        report,
        str(json_file),
        str(pdf_file),
    )


_LEVEL_CHOICES = [
    (1, "Level 1 — Brief  (1-page executive summary)"),
    (2, "Level 2 — Standard  (3-page: stage analysis + gap)"),
    (3, "Level 3 — Full  (5-page: deep integrity + remediation roadmap)"),
]

with gr.Blocks(title="STEM BIO-AI Local Trust Audit") as demo:
    gr.Markdown("# STEM BIO-AI Local Trust Audit")
    gr.Markdown(
        "Deterministic open-source pre-screen for bio/medical AI repositories.  \n"
        "Not clinical certification, regulatory clearance, or medical advice."
    )
    with gr.Row():
        repo_input = gr.Textbox(
            label="Public GitHub repository URL",
            placeholder="https://github.com/artic-network/fieldbioinformatics",
            scale=3,
        )
        level_input = gr.Radio(
            choices=[1, 2, 3],
            value=1,
            label="Report Level",
            info="1=brief 1p  |  2=standard 3p  |  3=full 5p",
        )
    run_button = gr.Button("Run audit", variant="primary")
    score_output  = gr.Textbox(label="Score")
    report_output = gr.Markdown(label="Markdown report")
    with gr.Row():
        json_output = gr.File(label="JSON result")
        pdf_output  = gr.File(label="PDF report")
    run_button.click(
        run_demo,
        inputs=[repo_input, level_input],
        outputs=[score_output, report_output, json_output, pdf_output],
    )
