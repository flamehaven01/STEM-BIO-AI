from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from mica_invoke import build_invocation_packet
from mica_runtime import build_session_report


def test_session_report_is_not_blocked_for_repo_root():
    report = build_session_report(REPO_ROOT)
    assert report["gate"] in {"PASS", "PASS_WITH_WARNINGS"}
    assert report["self_test"]["pct"] in {"CLOSED", "LEGACY"}


def test_guided_packet_contains_archive_and_playbook_targets():
    packet = build_invocation_packet(REPO_ROOT, "guided")
    names = [item["name"] for item in packet["read_targets"]]
    assert "mica_yaml" in names
    assert "archive" in names
    assert "playbook" in names
