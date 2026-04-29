from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

from .render import render_markdown, write_outputs
from .scanner import audit_repository

try:
    import gradio as gr
except ImportError as exc:  # pragma: no cover - only used by optional demo runtime
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


def run_demo(repo_url: str, mode: str, pages: int):
    tmp_path = Path(tempfile.gettempdir()) / "stem_ai_demo" / uuid4().hex
    tmp_path.mkdir(parents=True, exist_ok=True)
    repo = _clone_github(repo_url.strip(), tmp_path)
    result = audit_repository(repo)
    output_dir = tmp_path / "out"
    selected_pages = 1 if mode == "brief" else pages
    files = write_outputs(result, output_dir, mode, selected_pages, "all")
    report = render_markdown(result, mode, selected_pages)
    json_file = next(path for path in files if path.name.endswith("_experiment_results.json"))
    pdf_file = next(path for path in files if path.suffix == ".pdf")
    return (
        f"{result['score']['final_score']} / 100 ({result['score']['formal_tier']})",
        report,
        str(json_file),
        str(pdf_file),
    )


with gr.Blocks(title="STEM-AI Local Trust Audit") as demo:
    gr.Markdown("# STEM-AI Local Trust Audit")
    gr.Markdown(
        "Deterministic open-source pre-screen for bio/medical AI repositories. "
        "This is not clinical certification, regulatory clearance, or medical advice."
    )
    with gr.Row():
        repo_input = gr.Textbox(label="Public GitHub repository URL", placeholder="https://github.com/artic-network/fieldbioinformatics")
        mode_input = gr.Radio(["brief", "detailed"], value="brief", label="Report mode")
        pages_input = gr.Radio([3, 5], value=3, label="Detailed pages")
    run_button = gr.Button("Run audit", variant="primary")
    score_output = gr.Textbox(label="Score")
    report_output = gr.Markdown(label="Markdown report")
    json_output = gr.File(label="JSON result")
    pdf_output = gr.File(label="PDF report")
    run_button.click(
        run_demo,
        inputs=[repo_input, mode_input, pages_input],
        outputs=[score_output, report_output, json_output, pdf_output],
    )
