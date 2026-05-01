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
DISCLAIMER_TERMS = re.compile(
    r"(not for clinical|not for diagnostic|research use only|not medical advice|"
    r"not a medical device|not intended for clinical|not clinically validated|"
    r"not a clinical validation tool|not a regulatory submission|"
    r"not a substitute for clinical judgment|does not provide clinical diagnos(?:is|es)|"
    r"does not mean .*safe for clinical deployment|clinical deployment .*requires independent expert validation)",
    re.I,
)
BIAS_LIMITATION_TERMS = re.compile(r"\b(bias|fairness|limitation|limitations|generalizability|generalisation|not validated|validation cohort)\b", re.I)
COI_FUNDING_TERMS = re.compile(r"\b(conflict of interest|competing interest|funding|grant|sponsor|acknowledg(?:e)?ments?)\b", re.I)
HYPE_CLINICAL_CERTAINTY = re.compile(r"\b(clinically proven|clinically validated|clinical grade|diagnostic grade|safe for clinical deployment|deployment ready)\b", re.I)
HYPE_REGULATORY_APPROVAL = re.compile(r"\b(FDA approved|FDA cleared|CE marked|regulatory approved|regulatory cleared)\b", re.I)
HYPE_AUTONOMOUS_REPLACEMENT = re.compile(r"\b(replace (?:a )?(?:doctor|clinician|radiologist|pathologist)|without (?:a )?(?:doctor|clinician)|fully autonomous diagnosis|autonomous clinical decision)\b", re.I)
HYPE_BREAKTHROUGH = re.compile(r"\b(revolutionary|breakthrough|game[- ]changing|world[- ]class|best[- ]in[- ]class|state[- ]of[- ]the[- ]art)\b", re.I)
HYPE_UNIVERSAL_GENERALIZATION = re.compile(r"\b(all diseases|any disease|any patient|every patient|all clinical settings|universally applicable)\b", re.I)
HYPE_PERFECT_ACCURACY = re.compile(r"\b(100% accurate|perfect accuracy|zero false positives|zero false negatives|guaranteed accuracy|no errors)\b", re.I)
LIMITATIONS_SECTION = re.compile(r"(?m)^\s{0,3}#{1,6}\s+(limitations?|known limitations|validation boundaries|caveats)\b", re.I)
REGULATORY_FRAMEWORK_TERMS = re.compile(r"\b(FDA guidance|FDA submission|FDA regulatory|SaMD|software as a medical device|EU AI Act|MDR|HIPAA|IRB|IEC 62304|ISO 13485|ISO 14971|TRIPOD[- ]AI|CONSORT[- ]AI|regulatory framework)\b", re.I)
DEMOGRAPHIC_BIAS_TERMS = re.compile(r"\b(demographic|subgroup|sex|gender|age group|ethnicity|race|fairness|bias|under[- ]represented|validation cohort)\b", re.I)
REPRODUCIBILITY_TERMS = re.compile(r"\b(reproducib|replicat|rerun|recreate results|reproduce results|random seed|deterministic|environment\.yml|lockfile|checksum)\b", re.I)
STAGE2R_CLINICAL_DEPLOYMENT_CLAIMS = re.compile(r"\b(clinical decision support|patient-facing|diagnos(?:is|tic)|treatment recommendation|treatment guidance|triage|risk score|medical advice|clinical deployment|clinical workflow)\b", re.I)
STAGE2R_WORKFLOW_CLAIMS = re.compile(r"\b(quickstart|run|pipeline|workflow|command line|cli|demo|example notebook|pytest|unittest|test suite|continuous integration|CI)\b", re.I)
STAGE2R_ENTRYPOINT_TERMS = re.compile(r"(\[project\.scripts\]|console_scripts|entry_points|scripts\s*=|def\s+main\s*\()", re.I)
SECRET_TERMS = re.compile(r"(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|api[_-]?key\s*=\s*['\"][^'\"]{16,})")
PLACEHOLDER_SECRET_VALUES = re.compile(
    r"(super-secret|dummy|example|fake|placeholder|test[_-]?key|your[_-]?(api[_-]?)?key|"
    r"<(?:token|api[_-]?key)>|changeme|change-me)",
    re.I,
)
EXACT_PINNED_DEP = re.compile(r"(^|[A-Za-z0-9_.\-\]\)])\s*(==|===|@)\s*[^,\s;]+|sha256[:=]|--hash=sha256:", re.I)
LOOSE_DEP = re.compile(r"(>=|<=|~=|!=|>|<)")
PATIENT_METADATA = re.compile(r"(patient_|patient age|patient_sex|sample_id|collection_date|pregnan|municipality|lab_id)", re.I)
FAIL_OPEN = re.compile(r"(except(?:\s+Exception)?\s*:\s*(?:\r?\n\s*)?(?:pass|return\s+True))")
CHANGELOG_BUG_TERMS = re.compile(r"\b(fix(?:ed|es)?|bug|patch|regression|hotfix|breaking change|security|vulnerability|CVE)\b", re.I)
DATA_SOURCE_TERMS = re.compile(r"\b(IRB|institutional review board|data source|data availability|zenodo|figshare|GEO|SRA|PhysioNet|MIMIC|ClinicalTrials|dataset citation|download.*dataset)\b", re.I)
BIAS_MEASUREMENT_TERMS = re.compile(r"\b(subgroup analysis|demographic parity|equalized odds|disparate impact|per[- ]subgroup|cohort validation|AUROC|AUC score|performance gap|calibration curve|Brier score|tested on [0-9]+ patient)\b", re.I)
