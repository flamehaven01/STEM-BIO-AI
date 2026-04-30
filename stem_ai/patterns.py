from __future__ import annotations

import re


TEXT_EXTENSIONS = {
    ".md",
    ".rst",
    ".txt",
    ".toml",
    ".yml",
    ".yaml",
    ".json",
    ".py",
    ".sh",
    ".cfg",
    ".ini",
}
SKIP_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", "node_modules", ".venv", "venv"}
BIO_TERMS = re.compile(r"\b(bio|medical|clinical|virus|viral|genome|sequenc|variant|patient|diagnos|treatment)\b", re.I)
DISCLAIMER_TERMS = re.compile(r"(not for clinical|not for diagnostic|research use only|not medical advice)", re.I)
BIAS_LIMITATION_TERMS = re.compile(r"\b(bias|fairness|limitation|limitations|generalizability|generalisation|not validated|validation cohort)\b", re.I)
COI_FUNDING_TERMS = re.compile(r"\b(conflict of interest|competing interest|funding|grant|sponsor|acknowledg(?:e)?ments?)\b", re.I)
SECRET_TERMS = re.compile(r"(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|api[_-]?key\s*=\s*['\"][^'\"]{16,})")
EXACT_PINNED_DEP = re.compile(r"(^|[A-Za-z0-9_.\-\]\)])\s*(==|===|@)\s*[^,\s;]+|sha256[:=]|--hash=sha256:", re.I)
LOOSE_DEP = re.compile(r"(>=|<=|~=|!=|>|<)")
PATIENT_METADATA = re.compile(r"(patient_|patient age|patient_sex|sample_id|collection_date|pregnan|municipality|lab_id)", re.I)
FAIL_OPEN = re.compile(r"(except(?:\s+Exception)?\s*:\s*(?:\r?\n\s*)?(?:pass|return\s+True))")
