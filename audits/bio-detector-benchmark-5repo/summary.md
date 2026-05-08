# Bio Detector Benchmark Summary

## Biomni
- Score/Tier: 33 / T0 Rejected
- CA Severity: none
- BIO_smiles_surface_integrity: detected=200
  - BIO_smiles_surface_integrity:biomni/agent/a1.py:661:001 | warn | Suspicious or malformed SMILES-like string detected by conservative surface checks.
  - BIO_smiles_surface_integrity:biomni/agent/a1.py:1971:002 | warn | Suspicious or malformed SMILES-like string detected by conservative surface checks.
  - BIO_smiles_surface_integrity:biomni/agent/a1.py:1984:003 | warn | Suspicious or malformed SMILES-like string detected by conservative surface checks.
- BIO_smiles_parser_guard: not_detected=1
- BIO_silent_mock_fallback: detected=9
  - BIO_silent_mock_fallback:biomni/tool/cancer_biology.py:259:001 | warn | Runtime branch appears to redirect analysis into mock, demo, or simulated output behavior.
  - BIO_silent_mock_fallback:biomni/tool/genetics.py:724:001 | warn | Runtime branch appears to redirect analysis into mock, demo, or simulated output behavior.
  - BIO_silent_mock_fallback:biomni/tool/genetics.py:730:002 | warn | Runtime branch appears to redirect analysis into mock, demo, or simulated output behavior.
- BIO_trace_manifest: not_detected=1
- BIO_run_trace: detected=7
  - BIO_run_trace:biomni/tool/cancer_biology.py:627:001 | info | Known bio-tool subprocess call has no explicit timeout.
  - BIO_run_trace:biomni/tool/cancer_biology.py:642:002 | warn | Known bio-tool subprocess uses shell=True with likely external-input-tainted command construction.
  - BIO_run_trace:biomni/tool/cancer_biology.py:703:003 | info | Known bio-tool subprocess call has no explicit timeout.

## BioClaw
- Score/Tier: 48 / T1 Quarantine
- CA Severity: CA-INDIRECT
- BIO_smiles_surface_integrity: detected=10
  - BIO_smiles_surface_integrity:container/skills/bio-tools/pymol_render_template.py:26:001 | warn | Suspicious or malformed SMILES-like string detected by conservative surface checks.
  - BIO_smiles_surface_integrity:container/skills/bio-tools/volcano_plot_template.py:56:001 | warn | Suspicious or malformed SMILES-like string detected by conservative surface checks.
  - BIO_smiles_surface_integrity:container/skills/bio-tools/volcano_plot_template.py:57:002 | warn | Suspicious or malformed SMILES-like string detected by conservative surface checks.
- BIO_smiles_parser_guard: not_detected=1
- BIO_silent_mock_fallback: not_detected=1
- BIO_trace_manifest: detected=20
  - BIO_trace_manifest:.claude/skills/add-telegram-swarm/SKILL.md:196:001 | info | Traceability or runtime event schema keyword detected.
  - BIO_trace_manifest:.claude/skills/add-telegram/SKILL.md:174:001 | info | Traceability or runtime event schema keyword detected.
  - BIO_trace_manifest:.claude/skills/add-telegram/SKILL.md:210:002 | info | Traceability or runtime event schema keyword detected.
- BIO_run_trace: not_detected=1

## ClawBio
- Score/Tier: 67 / T2 Caution
- CA Severity: CA-DIRECT
- BIO_smiles_surface_integrity: detected=543
  - BIO_smiles_surface_integrity:bot/roboterri.py:56:001 | warn | Suspicious or malformed SMILES-like string detected by conservative surface checks.
  - BIO_smiles_surface_integrity:bot/roboterri.py:740:002 | warn | Suspicious or malformed SMILES-like string detected by conservative surface checks.
  - BIO_smiles_surface_integrity:bot/roboterri.py:757:003 | warn | Suspicious or malformed SMILES-like string detected by conservative surface checks.
- BIO_smiles_parser_guard: not_detected=1
- BIO_silent_mock_fallback: detected=44
  - BIO_silent_mock_fallback:bot/roboterri.py:500:001 | warn | Runtime branch appears to redirect analysis into mock, demo, or simulated output behavior.
  - BIO_silent_mock_fallback:bot/roboterri.py:507:002 | warn | Runtime branch appears to redirect analysis into mock, demo, or simulated output behavior.
  - BIO_silent_mock_fallback:bot/roboterri.py:517:003 | warn | Runtime branch appears to redirect analysis into mock, demo, or simulated output behavior.
- BIO_trace_manifest: not_detected=1
- BIO_run_trace: not_detected=1

## LabClaw
- Score/Tier: 28 / T0 Rejected
- CA Severity: none
- BIO_smiles_surface_integrity: not_detected=1
- BIO_smiles_parser_guard: not_detected=1
- BIO_silent_mock_fallback: not_detected=1
- BIO_trace_manifest: detected=19
  - BIO_trace_manifest:skills/bio/detect_common_wetlab_errors/SKILL.md:3:001 | info | Traceability or runtime event schema keyword detected.
  - BIO_trace_manifest:skills/bio/detect_common_wetlab_errors/SKILL.md:13:002 | info | Traceability or runtime event schema keyword detected.
  - BIO_trace_manifest:skills/bio/egocentric_view_to_structured_log/SKILL.md:13:001 | info | Traceability or runtime event schema keyword detected.
- BIO_run_trace: not_detected=1

## AI-Scientist
- Score/Tier: 33 / T0 Rejected
- CA Severity: none
- BIO_smiles_surface_integrity: detected=239
  - BIO_smiles_surface_integrity:ai_scientist/generate_ideas.py:511:001 | warn | Suspicious or malformed SMILES-like string detected by conservative surface checks.
  - BIO_smiles_surface_integrity:ai_scientist/llm.py:15:001 | warn | Suspicious or malformed SMILES-like string detected by conservative surface checks.
  - BIO_smiles_surface_integrity:ai_scientist/llm.py:16:002 | warn | Suspicious or malformed SMILES-like string detected by conservative surface checks.
- BIO_smiles_parser_guard: not_detected=1
- BIO_silent_mock_fallback: not_detected=1
- BIO_trace_manifest: not_detected=1
- BIO_run_trace: not_detected=1

