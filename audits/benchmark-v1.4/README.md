# STEM BIO-AI v1.4 Provider Benchmark Workspace

This workspace records provider-packet readiness and provider-response validation artifacts.

The benchmark does not make AI API calls. It measures whether local repository audits can produce compact provider-facing packets and whether saved provider advisory JSON responses satisfy the `finding_id` citation contract.

Expected artifacts:

```text
provider-response-local-10/benchmark_manifest.json
provider-response-local-10/packet_stats.jsonl
provider-response-local-10/packet_summary.json
provider-response-local-10/provider_response_validation.jsonl
provider-response-local-10/provider_failure_notes.md
provider-response-local-10/packets/*.json
```

Regenerate from the v1.3 local-10 manifest:

```powershell
python scripts\provider_packet_benchmark.py `
  --manifest audits\benchmark-v1.3\local-10\benchmark_manifest.json `
  --out audits\benchmark-v1.4\provider-response-local-10
```

Optional saved provider responses can be validated with:

```powershell
python scripts\provider_packet_benchmark.py `
  --responses path\to\provider_responses
```
