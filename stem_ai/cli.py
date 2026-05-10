from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .render import write_outputs
from .scanner import audit_repository


_LEVEL_MAP = {
    1: ("brief", 1),
    2: ("detailed", 3),
    3: ("detailed", 5),
}
_FORMAT_CHOICES = ["json", "md", "pdf", "all"]
_SUMMARY_CHOICES = ["full", "compact", "off"]
_ADVISORY_CHOICES = ["none", "validate", "packet", "call"]
_TIER_CHOICES = ["T0", "T1", "T2", "T3", "T4"]
_TIER_ORDER = {"T0": 0, "T1": 1, "T2": 2, "T3": 3, "T4": 4}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stem",
        description=(
            "STEM BIO-AI local evidence-surface scanner for bio/medical AI repositories.\n\n"
            "Workflow-oriented commands:\n"
            "  scan      Generate JSON / Markdown / PDF artifacts for a local repository\n"
            "  gate      Enforce a minimum triage tier for CI/CD pipelines\n"
            "  advisory  Run provider-neutral advisory validation and packet workflows\n\n"
            "Time-to-value shortcut:\n"
            "  stem <folder>  behaves the same as  stem scan <folder>"
        ),
        epilog=(
            "Common examples:\n"
            "  stem /path/to/repo\n"
            "  stem scan /path/to/repo --level 3 --format all --explain\n"
            "  stem gate /path/to/repo --min-tier T2\n"
            "  stem advisory packet /path/to/repo --output advisory_out\n"
            "  stem advisory check-response /path/to/repo --response provider_advisory.json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"STEM BIO-AI {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    scan = subparsers.add_parser(
        "scan",
        help="Run a local scan and generate report artifacts",
        description="Scan a local repository and generate deterministic STEM BIO-AI artifacts.",
    )
    _add_scan_arguments(scan, default_format="all", default_summary="full")

    audit = subparsers.add_parser(
        "audit",
        help="Backward-compatible alias for `scan`",
        description="Alias for `scan`. Kept for backward compatibility.",
    )
    _add_scan_arguments(audit, default_format="all", default_summary="full")

    gate = subparsers.add_parser(
        "gate",
        help="Run a scan and fail if the repository tier is below the required threshold",
        description="CI/CD-oriented workflow: run the scan and enforce a minimum triage tier.",
    )
    _add_shared_arguments(gate, default_format="json", default_summary="compact")
    gate.add_argument("target", help="Path to a local repository")
    gate.add_argument(
        "--min-tier",
        "--tier-gate",
        dest="min_tier",
        choices=_TIER_CHOICES,
        required=True,
        help="Minimum required tier; exit code 1 if the result is below this threshold",
    )

    advisory = subparsers.add_parser(
        "advisory",
        help="Provider-neutral advisory workflows",
        description="Prepare, validate, or execute advisory workflows without letting advisory output override deterministic scores.",
    )
    advisory_subparsers = advisory.add_subparsers(dest="advisory_command")
    advisory_subparsers.required = True

    advisory_validate = advisory_subparsers.add_parser(
        "validate",
        help="Run offline advisory validation against the deterministic result",
        description="Run the audit and attach offline advisory-validation metadata with no provider call.",
    )
    _add_shared_arguments(advisory_validate, default_format="json", default_summary="compact")
    advisory_validate.add_argument("target", help="Path to a local repository")

    advisory_packet = advisory_subparsers.add_parser(
        "packet",
        help="Export a provider-neutral advisory packet",
        description="Run the audit and export a sanitized advisory input packet for downstream provider review.",
    )
    _add_shared_arguments(advisory_packet, default_format="json", default_summary="compact")
    advisory_packet.add_argument("target", help="Path to a local repository")

    advisory_call = advisory_subparsers.add_parser(
        "call",
        help="Enter the explicit provider-call advisory workflow",
        description="Run the audit and execute the explicit provider-call advisory workflow.",
    )
    _add_shared_arguments(advisory_call, default_format="json", default_summary="compact")
    advisory_call.add_argument("target", help="Path to a local repository")

    advisory_response = advisory_subparsers.add_parser(
        "check-response",
        help="Validate a provider-produced advisory response JSON",
        description="Run the audit and validate a provider-produced advisory response file against the evidence ledger.",
    )
    _add_shared_arguments(advisory_response, default_format="json", default_summary="compact")
    advisory_response.add_argument("target", help="Path to a local repository")
    advisory_response.add_argument(
        "--response",
        "--advisory-response",
        dest="response",
        required=True,
        help="Path to a provider-produced advisory JSON response file",
    )

    return parser


def _add_scan_arguments(parser: argparse.ArgumentParser, *, default_format: str, default_summary: str) -> None:
    _add_shared_arguments(parser, default_format=default_format, default_summary=default_summary)
    parser.add_argument("target", help="Path to a local repository")
    parser.add_argument(
        "--advisory",
        choices=_ADVISORY_CHOICES,
        default="none",
        help="Compatibility path for advisory workflows; prefer `stem advisory validate|packet|call`",
    )
    parser.add_argument(
        "--advisory-response",
        default=None,
        help="Compatibility path for provider response validation; prefer `stem advisory check-response ... --response FILE`",
    )
    parser.add_argument(
        "--tier-gate",
        choices=_TIER_CHOICES,
        default=None,
        help="Compatibility path for CI gating; prefer `stem gate <folder> --min-tier ...`",
    )


def _add_shared_arguments(parser: argparse.ArgumentParser, *, default_format: str, default_summary: str) -> None:
    parser.set_defaults(default_summary=default_summary)
    parser.add_argument(
        "--level",
        type=int,
        choices=[1, 2, 3],
        default=1,
        help=(
            "Report depth: "
            "1=brief 1-page executive summary (default), "
            "2=detailed 3-page stage review, "
            "3=full 5-page evidence packet"
        ),
    )
    parser.add_argument(
        "--format",
        choices=_FORMAT_CHOICES,
        default=default_format,
        help="Artifact format to write",
    )
    parser.add_argument(
        "--out",
        "--output",
        dest="out",
        default="stem_output",
        help="Output directory for generated artifacts",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        default=False,
        help="Write a {stem}_explain.txt proof trace with file, line, snippet, and reason",
    )
    parser.add_argument(
        "--summary",
        choices=_SUMMARY_CHOICES,
        default=None,
        help="stdout summary mode: full, compact, or off",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Alias for `--summary off`",
    )


def _normalize_argv(argv: list[str]) -> list[str]:
    if not argv:
        return argv
    if argv[0] in {"scan", "audit", "gate", "advisory", "-h", "--help", "--version"}:
        return argv
    if argv[0].startswith("-"):
        return argv
    return ["scan", *argv]


def _validate_target(raw_target: str) -> Path:
    if raw_target.startswith(("http://", "https://")):
        raise SystemExit(
            "GitHub URL auditing is not enabled in the local CLI yet. "
            "Clone the repository first, then run: stem scan <local-folder>"
        )
    target = Path(raw_target).expanduser().resolve()
    if not target.exists():
        raise SystemExit(f"Target path does not exist: {target}")
    if not target.is_dir():
        raise SystemExit(f"Target must be a directory: {target}")
    return target


def _validate_optional_file(raw_path: str | None) -> Path | None:
    if raw_path is None:
        return None
    path = Path(raw_path).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"Advisory response file does not exist: {path}")
    if not path.is_file():
        raise SystemExit(f"Advisory response path must be a file: {path}")
    return path


def _resolve_summary_mode(args: argparse.Namespace) -> str:
    if getattr(args, "quiet", False):
        return "off"
    if getattr(args, "summary", None) is not None:
        return args.summary
    return getattr(args, "default_summary", "full")


def _bio_summary_line(result: dict) -> str | None:
    by_detector = result.get("detector_summary", {}).get("by_detector", {})
    hits = [key.replace("BIO_", "") for key, value in by_detector.items() if key.startswith("BIO_") and value.get("detected")]
    if not hits:
        return None
    return ", ".join(hits[:4]) + (f" (+{len(hits) - 4} more)" if len(hits) > 4 else "")


def _integrity_summary_line(result: dict) -> str | None:
    integrity = result.get("code_integrity", {})
    warnings = [key for key, value in integrity.items() if value.get("status") not in ("PASS", None)]
    if not warnings:
        return None
    return ", ".join(item.split("_", 1)[0] for item in warnings)


def _ast_scope_summary_line(result: dict) -> str | None:
    ast = result.get("ast_signal_summary", {})
    if not ast or not ast.get("file_limit_exceeded"):
        return None
    return (
        f"capped at {ast.get('files_considered', 'unknown')} / "
        f"{ast.get('files_total', 'unknown')} python files"
    )


def _workflow_label(command: str, advisory_command: str | None = None) -> str:
    if command == "gate":
        return "gate"
    if command == "advisory" and advisory_command is not None:
        return f"advisory {advisory_command}"
    return "scan"


def _evaluate_tier_gate(result: dict, required_tier: str | None) -> tuple[bool, str | None]:
    if required_tier is None:
        return True, None
    formal_tier = result["score"]["formal_tier"]
    actual_tier_key = formal_tier.split()[0]
    actual_rank = _TIER_ORDER.get(actual_tier_key, 0)
    required_rank = _TIER_ORDER[required_tier]
    passed = actual_rank >= required_rank
    verdict = "PASS" if passed else "FAIL"
    return passed, f"{verdict} ({formal_tier} vs required {required_tier})"


def _print_full_summary(
    result: dict,
    *,
    workflow: str,
    level: int,
    mode: str,
    pages: int,
    output_dir: Path,
    created: list[Path],
    advisory_mode: str,
    advisory_response: Path | None,
    gate_message: str | None,
) -> None:
    score = result["score"]
    classification = result.get("classification", {})

    print("STEM BIO-AI scan complete")
    print(f"Workflow:    {workflow}")
    print(f"Target:      {result['target']['name']}")
    print(f"Level:       {level}  ({mode}, {pages}p)")
    print()

    print(f"Score:       {score['final_score']} / 100  ({score['formal_tier']})")
    print(f"  Stage 1:   {score['stage_1_readme_intent']} / 100   (README evidence)")
    print(f"  Stage 2R:  {score['stage_2_repo_local_consistency']} / 100   (repo consistency)")
    print(f"  Stage 3:   {score['stage_3_code_bio']} / 100   (code + bio)")
    rep_score = result.get("replication_score")
    rep_tier = result.get("replication_tier")
    if rep_score is not None:
        print(f"  Stage 4:   {rep_score} / 100   (replication {rep_tier})")

    ca = classification.get("ca_severity", "none")
    if ca != "none":
        clinical_line = f"Clinical:    {ca}"
        if classification.get("t0_hard_floor"):
            clinical_line += "  [T0 HARD FLOOR]"
        elif classification.get("score_cap") is not None:
            clinical_line += f"  [cap={classification['score_cap']}]"
        print(clinical_line)

    integrity_line = _integrity_summary_line(result)
    if integrity_line:
        print(f"Integrity:   WARN ({integrity_line})")

    bio_line = _bio_summary_line(result)
    if bio_line:
        print(f"Bio:         {bio_line}")

    ast_line = _ast_scope_summary_line(result)
    if ast_line:
        print(f"AST Scope:   {ast_line}")

    regulatory = result.get("regulatory_basis", {})
    if regulatory.get("review_required"):
        reasons = ", ".join(regulatory.get("review_reasons", []))
        print(f"Regulatory:  review required ({reasons})")

    if advisory_mode == "none" and advisory_response is None:
        print("AI:          not used (deterministic only)")
    else:
        ai_status = result.get("ai_advisory", {})
        provider = ai_status.get("provider", "none")
        status = "packet_ready" if advisory_mode == "packet" else ai_status.get("status", "not_run")
        print(f"AI:          {status} (provider={provider})")

    if gate_message is not None:
        print(f"Gate:        {gate_message}")

    risks = result.get("notable_risks", [])
    if risks:
        print()
        limit = min(len(risks), 3)
        print(f"Action items ({len(risks)} total):")
        for risk in risks[:limit]:
            print(f"  - {risk}")
        if len(risks) > limit:
            print(f"  ... +{len(risks) - limit} more (see report)")

    print()
    print(f"Output:      {output_dir}")
    for path in created:
        print(f"  {path.name}")


def _print_compact_summary(
    result: dict,
    *,
    workflow: str,
    output_dir: Path,
    created: list[Path],
    gate_message: str | None,
) -> None:
    score = result["score"]
    print(f"STEM BIO-AI | {workflow} | {score['formal_tier']} | {score['final_score']}/100")
    print(f"Target: {result['target']['name']}")

    classification = result.get("classification", {})
    if classification.get("ca_severity", "none") != "none":
        suffix = ""
        if classification.get("t0_hard_floor"):
            suffix = " [T0 HARD FLOOR]"
        elif classification.get("score_cap") is not None:
            suffix = f" [cap={classification['score_cap']}]"
        print(f"Clinical: {classification['ca_severity']}{suffix}")

    if gate_message is not None:
        print(f"Gate: {gate_message}")

    ast_line = _ast_scope_summary_line(result)
    if ast_line:
        print(f"AST: {ast_line}")

    print(f"Artifacts: {len(created)} -> {output_dir}")


def _print_summary(
    result: dict,
    *,
    workflow: str,
    level: int,
    mode: str,
    pages: int,
    output_dir: Path,
    created: list[Path],
    advisory_mode: str,
    advisory_response: Path | None,
    summary_mode: str,
    gate_message: str | None,
) -> None:
    if summary_mode == "off":
        return
    if summary_mode == "compact":
        _print_compact_summary(
            result,
            workflow=workflow,
            output_dir=output_dir,
            created=created,
            gate_message=gate_message,
        )
        return
    _print_full_summary(
        result,
        workflow=workflow,
        level=level,
        mode=mode,
        pages=pages,
        output_dir=output_dir,
        created=created,
        advisory_mode=advisory_mode,
        advisory_response=advisory_response,
        gate_message=gate_message,
    )


def _execute_scan(
    *,
    target: Path,
    level: int,
    fmt: str,
    out_dir: str,
    explain: bool,
    advisory_mode: str,
    advisory_response: Path | None,
    tier_gate: str | None,
    summary_mode: str,
    workflow: str,
) -> int:
    mode, pages = _LEVEL_MAP[level]
    result = audit_repository(target, advisory=advisory_mode, advisory_response_path=advisory_response)
    output_dir = Path(out_dir).expanduser().resolve()
    created = write_outputs(result, output_dir, mode, pages, fmt, explain=explain)
    gate_passed, gate_message = _evaluate_tier_gate(result, tier_gate)

    _print_summary(
        result,
        workflow=workflow,
        level=level,
        mode=mode,
        pages=pages,
        output_dir=output_dir,
        created=created,
        advisory_mode=advisory_mode,
        advisory_response=advisory_response,
        summary_mode=summary_mode,
        gate_message=gate_message,
    )
    return 0 if gate_passed else 1


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    parsed = parser.parse_args(_normalize_argv(list(sys.argv[1:] if argv is None else argv)))
    if parsed.command is None:
        parser.print_help()
        return 2

    summary_mode = _resolve_summary_mode(parsed)

    if parsed.command in {"scan", "audit"}:
        target = _validate_target(parsed.target)
        advisory_response = _validate_optional_file(parsed.advisory_response)
        return _execute_scan(
            target=target,
            level=parsed.level,
            fmt=parsed.format,
            out_dir=parsed.out,
            explain=parsed.explain,
            advisory_mode=parsed.advisory,
            advisory_response=advisory_response,
            tier_gate=parsed.tier_gate,
            summary_mode=summary_mode,
            workflow="scan",
        )

    if parsed.command == "gate":
        target = _validate_target(parsed.target)
        return _execute_scan(
            target=target,
            level=parsed.level,
            fmt=parsed.format,
            out_dir=parsed.out,
            explain=parsed.explain,
            advisory_mode="none",
            advisory_response=None,
            tier_gate=parsed.min_tier,
            summary_mode=summary_mode,
            workflow="gate",
        )

    if parsed.command == "advisory":
        target = _validate_target(parsed.target)
        advisory_response = None
        advisory_mode = "none"
        if parsed.advisory_command == "validate":
            advisory_mode = "validate"
        elif parsed.advisory_command == "packet":
            advisory_mode = "packet"
        elif parsed.advisory_command == "call":
            advisory_mode = "call"
        elif parsed.advisory_command == "check-response":
            advisory_response = _validate_optional_file(parsed.response)
        return _execute_scan(
            target=target,
            level=parsed.level,
            fmt=parsed.format,
            out_dir=parsed.out,
            explain=parsed.explain,
            advisory_mode=advisory_mode,
            advisory_response=advisory_response,
            tier_gate=None,
            summary_mode=summary_mode,
            workflow=_workflow_label(parsed.command, parsed.advisory_command),
        )

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
