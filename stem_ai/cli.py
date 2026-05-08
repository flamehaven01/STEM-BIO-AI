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
_ADVISORY_CHOICES = ["none", "validate", "packet", "call"]
_TIER_CHOICES = ["T0", "T1", "T2", "T3", "T4"]
_TIER_ORDER = {"T0": 0, "T1": 1, "T2": 2, "T3": 3, "T4": 4}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stem",
        usage=(
            "stem <folder> [--level 1|2|3] [--format json|md|pdf|all] [--out DIR] [--explain] [--advisory MODE] [--advisory-response FILE]\n"
            "       stem audit <folder> [--level 1|2|3] [--format json|md|pdf|all]"
            " [--out DIR] [--explain] [--advisory MODE] [--advisory-response FILE]"
            " [--tier-gate T0..T4] [--quiet]"
        ),
        description="STEM BIO-AI local evidence-surface scan for bio/medical AI repositories.",
        epilog=(
            "Examples:\n"
            "  stem /path/to/bio-ai-repo\n"
            "  stem /path/to/bio-ai-repo --level 2\n"
            "  stem /path/to/bio-ai-repo --level 3 --format all --out stem_output\n"
            "  stem /path/to/bio-ai-repo --explain\n"
            "  stem /path/to/bio-ai-repo --advisory validate\n"
            "  stem /path/to/bio-ai-repo --advisory packet\n"
            "  stem /path/to/bio-ai-repo --advisory call\n"
            "  stem /path/to/bio-ai-repo --advisory-response provider_advisory.json\n"
            "\n"
            "CI/CD gate examples:\n"
            "  stem /path/to/repo --tier-gate T2 --quiet        # fail if below T2\n"
            "  stem /path/to/repo --tier-gate T3 --format json   # gate + json output"
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
    audit.add_argument(
        "--explain",
        action="store_true",
        default=False,
        help="Write a {stem}_explain.txt file listing every evidence finding with file, line, snippet, and reason",
    )
    audit.add_argument(
        "--advisory",
        choices=_ADVISORY_CHOICES,
        default="none",
        help="Run offline advisory validation, export a provider-neutral packet, or enter explicit advisory call mode",
    )
    audit.add_argument(
        "--advisory-response",
        default=None,
        help="Validate a provider-produced advisory JSON response against this audit's evidence ledger",
    )
    audit.add_argument(
        "--tier-gate",
        choices=_TIER_CHOICES,
        default=None,
        help="CI gate: exit non-zero (exit code 1) if audit tier is below this threshold",
    )
    audit.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress human-readable stdout summary (artifacts are still written)",
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


def _bio_summary_line(result: dict) -> str | None:
    """Build a one-line bio diagnostics summary from detector_summary."""
    by_detector = result.get("detector_summary", {}).get("by_detector", {})
    hits = [k.replace("BIO_", "") for k, v in by_detector.items()
            if k.startswith("BIO_") and v.get("detected")]
    if not hits:
        return None
    return ", ".join(hits[:4]) + (f" (+{len(hits) - 4} more)" if len(hits) > 4 else "")


def _integrity_summary_line(result: dict) -> str | None:
    """Build a one-line code integrity summary from C1-C4."""
    integrity = result.get("code_integrity", {})
    warnings = [k for k, v in integrity.items() if v.get("status") not in ("PASS", None)]
    if not warnings:
        return None
    return ", ".join(w.split("_", 1)[0] for w in warnings)


def _print_summary(result: dict, args: argparse.Namespace, mode: str, pages: int, output_dir: Path, created: list[Path]) -> None:
    """Print enriched human-readable stdout summary."""
    score = result["score"]
    classification = result.get("classification", {})

    # Core identity
    print("STEM BIO-AI local evidence-surface scan complete")
    print(f"Target:      {result['target']['name']}")
    print(f"Level:       {args.level}  ({mode}, {pages}p)")
    print()

    # Score block
    print(f"Score:       {score['final_score']} / 100  ({score['formal_tier']})")
    print(f"  Stage 1:   {score['stage_1_readme_intent']} / 100   (README evidence)")
    print(f"  Stage 2R:  {score['stage_2_repo_local_consistency']} / 100   (repo consistency)")
    print(f"  Stage 3:   {score['stage_3_code_bio']} / 100   (code + bio)")

    # Replication lane (v1.3.0+)
    rep_score = result.get("replication_score")
    rep_tier = result.get("replication_tier")
    if rep_score is not None:
        print(f"  Stage 4:   {rep_score} / 100   (replication {rep_tier})")

    # Clinical adjacency
    ca = classification.get("ca_severity", "none")
    if ca != "none":
        print(f"Clinical:    {ca}", end="")
        if classification.get("t0_hard_floor"):
            print("  [T0 HARD FLOOR]", end="")
        elif classification.get("score_cap") is not None:
            print(f"  [cap={classification['score_cap']}]", end="")
        print()

    # Code integrity (v1.1.3+)
    integrity_line = _integrity_summary_line(result)
    if integrity_line:
        print(f"Integrity:   WARN ({integrity_line})")

    # Bio diagnostics (v1.5.10+)
    bio_line = _bio_summary_line(result)
    if bio_line:
        print(f"Bio:         {bio_line}")

    # Regulatory basis (v1.6.0+)
    reg = result.get("regulatory_basis", {})
    if reg.get("review_required"):
        reasons = ", ".join(reg.get("review_reasons", []))
        print(f"Regulatory:  review required ({reasons})")

    # AI usage (always displayed -- trust transparency)
    if args.advisory == "none" and args.advisory_response is None:
        print("AI:          not used (deterministic only)")
    else:
        ai_status = result.get("ai_advisory", {})
        provider = ai_status.get("provider", "none")
        status = "packet_ready" if args.advisory == "packet" else ai_status.get("status", "not_run")
        print(f"AI:          {status} (provider={provider})")

    # Remediation hints from notable_risks (v1.2.0+)
    risks = result.get("notable_risks", [])
    if risks:
        print()
        limit = min(len(risks), 3)
        print(f"Action items ({len(risks)} total):")
        for risk in risks[:limit]:
            print(f"  - {risk}")
        if len(risks) > limit:
            print(f"  ... +{len(risks) - limit} more (see report)")

    # Output listing
    print()
    print(f"Output:      {output_dir}")
    for path in created:
        print(f"  {path.name}")


def run_audit(args: argparse.Namespace) -> int:
    target = _validate_target(args.target)
    advisory_response = _validate_optional_file(args.advisory_response)
    mode, pages = _LEVEL_MAP[args.level]

    result = audit_repository(target, advisory=args.advisory, advisory_response_path=advisory_response)
    output_dir = Path(args.out).expanduser().resolve()
    created = write_outputs(result, output_dir, mode, pages, args.format, explain=args.explain)

    if not args.quiet:
        _print_summary(result, args, mode, pages, output_dir, created)

    # CI/CD tier gate: exit non-zero if actual tier is below the required threshold
    if args.tier_gate is not None:
        formal_tier = result["score"]["formal_tier"]
        actual_tier_key = formal_tier.split()[0]  # "T3 Supervised" -> "T3"
        actual_rank = _TIER_ORDER.get(actual_tier_key, 0)
        required_rank = _TIER_ORDER[args.tier_gate]
        if actual_rank < required_rank:
            if not args.quiet:
                print(f"\nGATE FAIL: {formal_tier} does not meet --tier-gate {args.tier_gate}")
            return 1

    return 0


def _validate_optional_file(raw_path: str | None) -> Path | None:
    if raw_path is None:
        return None
    path = Path(raw_path).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"Advisory response file does not exist: {path}")
    if not path.is_file():
        raise SystemExit(f"Advisory response path must be a file: {path}")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    parsed = parser.parse_args(_normalize_argv(list(sys.argv[1:] if argv is None else argv)))
    if parsed.command == "audit":
        return run_audit(parsed)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
