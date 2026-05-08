# Bio Detector Benchmark Summary (rerun)

## Biomni
- Score/Tier: 33 / T0 Rejected
- CA Severity: none
- BIO_smiles_surface_integrity: detected=8
  - BIO_smiles_surface_integrity:biomni/tool/genetics.py:1327:001 | warn | {'smiles_text': 'bp)', 'issues': ['unbalanced_parentheses']}
  - BIO_smiles_surface_integrity:biomni/tool/genetics.py:1328:002 | warn | {'smiles_text': 'bp)', 'issues': ['unbalanced_parentheses']}
  - BIO_smiles_surface_integrity:biomni/tool/microbiology.py:647:001 | warn | {'smiles_text': 'KB)', 'issues': ['unbalanced_parentheses']}
- BIO_smiles_parser_guard: not_detected=1
- BIO_silent_mock_fallback: detected=9
  - BIO_silent_mock_fallback:biomni/tool/cancer_biology.py:259:001 | warn | {'reason': 'runtime_mock_toggle_controls_output_path', 'recommended_severity': 'warn'}
  - BIO_silent_mock_fallback:biomni/tool/genetics.py:724:001 | warn | {'reason': 'runtime_mock_toggle_controls_output_path', 'recommended_severity': 'warn'}
  - BIO_silent_mock_fallback:biomni/tool/genetics.py:730:002 | warn | {'reason': 'runtime_mock_toggle_controls_output_path', 'recommended_severity': 'warn'}
- BIO_trace_manifest: not_detected=1
- BIO_run_trace: detected=7
  - BIO_run_trace:biomni/tool/cancer_biology.py:627:001 | info | {'call_name': 'subprocess.run', 'bio_tool': 'samtools', 'shell_true': False, 'external_input_taint': True, 'string_command': False, 'timeout_present': False, 'evidence_mode': 'observation_only'}
  - BIO_run_trace:biomni/tool/cancer_biology.py:642:002 | warn | {'call_name': 'subprocess.run', 'bio_tool': 'samtools', 'shell_true': True, 'external_input_taint': True, 'string_command': False, 'timeout_present': False, 'evidence_mode': 'observation_only'}
  - BIO_run_trace:biomni/tool/cancer_biology.py:703:003 | info | {'call_name': 'subprocess.run', 'bio_tool': 'bcftools', 'shell_true': False, 'external_input_taint': True, 'string_command': False, 'timeout_present': False, 'evidence_mode': 'observation_only'}

## BioClaw
- Score/Tier: 48 / T1 Quarantine
- CA Severity: CA-INDIRECT
- BIO_smiles_surface_integrity: not_detected=1
- BIO_smiles_parser_guard: not_detected=1
- BIO_silent_mock_fallback: not_detected=1
- BIO_trace_manifest: not_detected=1
- BIO_run_trace: not_detected=1

## ClawBio
- Score/Tier: 67 / T2 Caution
- CA Severity: CA-DIRECT
- BIO_smiles_surface_integrity: detected=4
  - BIO_smiles_surface_integrity:skills/rnaseq-de/rnaseq_de.py:153:001 | warn | {'smiles_text': 'PC1', 'issues': ['unclosed_ring_label']}
  - BIO_smiles_surface_integrity:skills/rnaseq-de/rnaseq_de.py:154:002 | warn | {'smiles_text': 'PC2', 'issues': ['unclosed_ring_label']}
  - BIO_smiles_surface_integrity:skills/rnaseq-de/rnaseq_de.py:331:003 | warn | {'smiles_text': 'PC1', 'issues': ['unclosed_ring_label']}
- BIO_smiles_parser_guard: not_detected=1
- BIO_silent_mock_fallback: detected=44
  - BIO_silent_mock_fallback:bot/roboterri.py:500:001 | warn | {'reason': 'runtime_mock_toggle_controls_output_path', 'recommended_severity': 'warn'}
  - BIO_silent_mock_fallback:bot/roboterri.py:507:002 | warn | {'reason': 'runtime_mock_toggle_controls_output_path', 'recommended_severity': 'warn'}
  - BIO_silent_mock_fallback:bot/roboterri.py:517:003 | warn | {'reason': 'runtime_mock_toggle_controls_output_path', 'recommended_severity': 'warn'}
- BIO_trace_manifest: not_detected=1
- BIO_run_trace: not_detected=1

## LabClaw
- Score/Tier: 28 / T0 Rejected
- CA Severity: none
- BIO_smiles_surface_integrity: not_detected=1
- BIO_smiles_parser_guard: not_detected=1
- BIO_silent_mock_fallback: not_detected=1
- BIO_trace_manifest: not_detected=1
- BIO_run_trace: not_detected=1

## AI-Scientist
- Score/Tier: 33 / T0 Rejected
- CA Severity: none
- BIO_smiles_surface_integrity: not_detected=1
- BIO_smiles_parser_guard: not_detected=1
- BIO_silent_mock_fallback: not_detected=1
- BIO_trace_manifest: not_detected=1
- BIO_run_trace: not_detected=1

