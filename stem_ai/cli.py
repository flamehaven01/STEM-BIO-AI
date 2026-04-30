from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .render import write_outputs
from .scanner import audit_repository


_LEVEL_MAP = {
    1: ("brief",    1),
    2: ("detailed", 3),
    3: ("detailed", 5),
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stem",
        usage=(
            "stem <folder> [--level 1|2|3] [--format json|md|pdf|all] [--out DIR]\n"
            "       stem audit <folder> [--level 1|2|3] [--format json|md|pdf|all] [--out DIR]"
        ),
        description="STEM BIO-AI local evidence-surface scan for bio/medical AI repositories.",
        epilog=(
            "Examples:\n"
            "  stem /path/to/bio-ai-repo\n"
            "  stem /path/to/bio-ai-repo --level 2\n"
            "  stem /path/to/bio-ai-repo --level 3 --format all --out stem_output"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"STEM BIO-AI {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    audit = subparsers.add_parser("audit", help="Audit a local repository")
    audit.add_argument("target", help="Path to a local repository")
    audit.add_argument(
        "--level",
        type=int,
        choices=[1, 2, 3],
        default=1,
        help=(
            "Report depth: "
            "1=brief 1-page executive summary (default), "
            "2=detailed 3-page with stage analysis, "
            "3=detailed 5-page with deep integrity + remediation"
        ),
    )
    audit.add_argument(
        "--format",
        choices=["json", "md", "pdf", "all"],
        default="all",
        help="Output format",
    )
    audit.add_argument(
        "--out",
        default="stem_output",
        help="Output directory",
    )
    return parser


def _normalize_argv(argv: list[str]) -> list[str]:
    if not argv:
        return argv
    if argv[0] in {"audit", "-h", "--help", "--version"}:
        return argv
    if argv[0].startswith("-"):
        return argv
    # Time-to-value shortcut: `stem <folder>` behaves as `stem audit <folder>`.
    return ["audit", *argv]


def _validate_target(raw_target: str) -> Path:
    if raw_target.startswith(("http://", "https://")):
        raise SystemExit(
            "GitHub URL auditing is not enabled in the local CLI yet. "
            "Clone the repository first, then run: stem audit <local-folder>"
        )
    target = Path(raw_target).expanduser().resolve()
    if not target.exists():
        raise SystemExit(f"Target path does not exist: {target}")
    if not target.is_dir():
        raise SystemExit(f"Target must be a directory: {target}")
    return target


def run_audit(args: argparse.Namespace) -> int:
    target = _validate_target(args.target)
    mode, pages = _LEVEL_MAP[args.level]

    result = audit_repository(target)
    output_dir = Path(args.out).expanduser().resolve()
    created = write_outputs(result, output_dir, mode, pages, args.format)

    score = result["score"]
    print("STEM BIO-AI local evidence-surface scan complete")
    print(f"Target:  {result['target']['name']}")
    print(f"Level:   {args.level}  ({mode}, {pages}p)")
    print(f"Score:   {score['final_score']} / 100  ({score['formal_tier']})")
    print(f"Output:  {output_dir}")
    for path in created:
        print(f"  {path.name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    parsed = parser.parse_args(_normalize_argv(list(sys.argv[1:] if argv is None else argv)))
    if parsed.command == "audit":
        return run_audit(parsed)
    parser.print_help()
    return 2
