# STEM BIO-AI Risk Taxonomy

Standardized finding categories for Claim Matrix and audit reports.

## Finding Categories

| Category | Definition | Example Trigger | Typical Severity |
|----------|-----------|-----------------|-----------------|
| Documentation-Reality Divergence | README claims exceed what code evidence supports | "production-ready" label on repo with no tests | High |
| Insecure Default | Security controls exist but default config bypasses them | Rate limiter disabled when USE_JOB_QUEUE=false | High-Critical |
| Operational Exposure | Runtime surface exposes unsafe patterns to users | Admin dashboard unauthenticated by default | High |
| Mock-to-Production Ambiguity | Placeholder/mock code presented as functional output | Drug discovery function that appends ASCII to SMILES | Critical |
| Licensing Ambiguity | License missing, contradictory, or incomplete | No LICENSE file; individual files say "All Rights Reserved" | Medium |
| Scientific Validity Surface Gap | Claimed scientific use not supported by validation evidence | Survival analysis script with no statistical tests | High |
| Governance Surface Deficiency | Missing change control, review discipline, stewardship markers | No CHANGELOG, no CONTRIBUTING, no SECURITY policy | Medium |
| Validation Surface Gap | Validators check format not substance | CI validates SKILL.md structure, not code correctness | Medium-High |
| Trust-Surface Inconsistency | Mixed signals across different repository surfaces | README says "research-only" but marketing says "production" | Medium |
| Ecosystem-Level Risk Pattern | Pattern recurring across multiple repositories in audit | 8/10 repos score T0 for same structural reasons | High |

## Severity Definitions

| Level | Definition | Institutional Impact |
|-------|-----------|---------------------|
| Critical | Immediate safety or operational risk if deployed | Blocks any institutional consideration |
| High | Institutional reuse blocked without remediation | Requires specific remediation before next review |
| Medium | Review required before institutional adoption | Manageable with governance overlay or expert review |
| Low | Improvement recommended, not blocking | Track for future audit, no immediate action required |

## Confidence Definitions

| Level | Definition | Evidence Basis |
|-------|-----------|---------------|
| High | Directly observed in code, config, or workflow | Specific file path, line number, or commit hash |
| Moderate | Indirectly supported through combination of signals | Multiple surface indicators pointing same direction |
| Low | Surface-level observation, interpretation margin present | README text or incomplete evidence chain |
