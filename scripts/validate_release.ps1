param(
    [string]$ExpectedVersion = "1.3.2",
    [string]$OutputRoot = "tmp\release_validation",
    [string]$SlopDetectorPath = "D:\Sanctum\ai-slop-detector",
    [switch]$WithSlop
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$versionSlug = "v" + ($ExpectedVersion -replace "\.", "_")
$outDir = Join-Path $repoRoot (Join-Path $OutputRoot "$($versionSlug)_$timestamp")

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Body
    )
    Write-Host ""
    Write-Host "==> $Name"
    & $Body
    Write-Host "PASS: $Name"
}

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )
    if (-not $Condition) {
        throw $Message
    }
}

Push-Location $repoRoot
try {
    Invoke-Step "CLI version is $ExpectedVersion" {
        $version = python -m stem_ai --version
        Write-Host $version
        Assert-True ($version -eq "STEM BIO-AI $ExpectedVersion") "Unexpected CLI version: $version"
    }

    Invoke-Step "pytest regression suite" {
        python -m pytest -q
    }

    Invoke-Step "package build" {
        python -m build --no-isolation
    }

    Invoke-Step "local audit artifacts with --explain" {
        New-Item -ItemType Directory -Force -Path $outDir | Out-Null
        python -m stem_ai . --level 3 --format all --out $outDir --explain
    }

    Invoke-Step "audit JSON contract" {
        $jsonFiles = @(Get-ChildItem -LiteralPath $outDir -Filter "*_experiment_results.json")
        Assert-True ($jsonFiles.Count -eq 1) "Expected one experiment_results JSON, found $($jsonFiles.Count)"
        $result = Get-Content -LiteralPath $jsonFiles[0].FullName -Raw | ConvertFrom-Json

        Assert-True ($result.stem_ai_version -eq $ExpectedVersion) "stem_ai_version mismatch: $($result.stem_ai_version)"
        Assert-True ($result.schema_version -eq "stem-ai-local-cli-result-v1.3") "schema_version mismatch: $($result.schema_version)"
        Assert-True ($null -ne $result.evidence_ledger -and $result.evidence_ledger.Count -gt 0) "evidence_ledger missing or empty"
        Assert-True ($null -ne $result.detector_summary) "detector_summary missing"
        Assert-True ($null -ne $result.ast_signal_summary) "ast_signal_summary missing"
        Assert-True ($null -ne $result.stage_4_rubric) "stage_4_rubric missing"
        Assert-True ($null -ne $result.replication_score) "replication_score missing"
        Assert-True ([string]$result.replication_tier -match "^R[0-4]$") "replication_tier invalid: $($result.replication_tier)"
        Assert-True ($null -ne $result.reasoning_model) "reasoning_model missing"
        Assert-True ($result.reasoning_model.version -eq "stem-bio-ai-reasoning-v1.3.2") "reasoning_model version mismatch: $($result.reasoning_model.version)"
        Assert-True ($result.reasoning_model.policy.final_score_override -eq $false) "reasoning_model must not override final score"
        Assert-True ($null -ne $result.reasoning_model.lane_coherence) "reasoning_model.lane_coherence missing"
        Assert-True ($null -ne $result.reasoning_model.uncertainty_budget) "reasoning_model.uncertainty_budget missing"
        Assert-True ($null -ne $result.reasoning_model.evidence_risk_gate) "reasoning_model.evidence_risk_gate missing"

        $badIds = @($result.evidence_ledger | Where-Object { [string]$_.finding_id -match "\\" })
        Assert-True ($badIds.Count -eq 0) "finding_id contains Windows backslash"

        $s4Findings = @($result.evidence_ledger | Where-Object { [string]$_.detector -like "S4_*" })
        Assert-True ($s4Findings.Count -gt 0) "Stage 4 findings missing from evidence_ledger"

        Write-Host "score=$($result.score.final_score) tier=$($result.score.formal_tier)"
        Write-Host "replication_score=$($result.replication_score) replication_tier=$($result.replication_tier)"
        Write-Host "evidence_ledger=$($result.evidence_ledger.Count)"
    }

    Invoke-Step "explain artifact contract" {
        $explainFiles = @(Get-ChildItem -LiteralPath $outDir -Filter "*_explain.txt")
        Assert-True ($explainFiles.Count -eq 1) "Expected one explain artifact, found $($explainFiles.Count)"
        $explain = Get-Content -LiteralPath $explainFiles[0].FullName -Raw
        Assert-True ($explain.Contains("STEM BIO-AI Explain Report")) "Explain header missing"
        Assert-True ($explain.Contains("finding_id:")) "Explain finding_id lines missing"
        Assert-True ($explain.Contains("AST Signal Summary")) "Explain AST summary missing"
        Assert-True ($explain.Contains("Stage 4 Replication Rubric")) "Explain Stage 4 rubric missing"
        Assert-True ($explain.Contains("DISCLAIMER:")) "Explain disclaimer missing"
    }

    Invoke-Step "markdown and PDF artifacts exist" {
        $mdFiles = @(Get-ChildItem -LiteralPath $outDir -Filter "*_report.md")
        $pdfFiles = @(Get-ChildItem -LiteralPath $outDir -Filter "*.pdf")
        Assert-True ($mdFiles.Count -eq 1) "Expected one Markdown report, found $($mdFiles.Count)"
        Assert-True ($pdfFiles.Count -eq 1) "Expected one PDF report, found $($pdfFiles.Count)"
        Assert-True ($pdfFiles[0].Length -gt 1000) "PDF report appears too small"
    }

    if ($WithSlop -and (Test-Path -LiteralPath $SlopDetectorPath)) {
        Invoke-Step "slop detector clean scan" {
            $slopOut = Join-Path $outDir "slop_report.json"
            Push-Location $SlopDetectorPath
            try {
                python -m slop_detector.cli --project $repoRoot --json --output $slopOut
            }
            finally {
                Pop-Location
            }
            $slop = Get-Content -LiteralPath $slopOut -Raw | ConvertFrom-Json
            Assert-True ($slop.overall_status -eq "clean") "Slop status is not clean: $($slop.overall_status)"
            Assert-True ([int]$slop.deficit_files -eq 0) "Slop deficit_files is not zero: $($slop.deficit_files)"
            Write-Host "slop overall_status=$($slop.overall_status) clean_files=$($slop.clean_files) deficit_files=$($slop.deficit_files)"
        }
    }
    else {
        Write-Host ""
        Write-Host "SKIP: external slop detector clean scan (pass -WithSlop to enable)"
    }

    Write-Host ""
    Write-Host "STEM BIO-AI v$ExpectedVersion validation PASSED"
    Write-Host "Artifacts: $outDir"
}
finally {
    Pop-Location
}
