#requires -Version 5.1
<#
  From the repository root:
    .\scripts\verify_project.ps1
    .\scripts\verify_project.ps1 -Submission
    .\scripts\verify_project.ps1 -FullRebuild

  Validates data, test fixtures, CSV round-tripping and repo/submission layout.
  Validation report goes into TEMP, not the tracked working tree.
#>
param(
    [string]$Python = 'python',
    [switch]$FullRebuild,
    [switch]$Submission
)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Report = Join-Path ([System.IO.Path]::GetTempPath()) ("lifeline_validation_{0}.txt" -f [guid]::NewGuid().ToString('N'))

function Invoke-Python {
    param([string[]]$Arguments)
    Write-Host ("> python " + ($Arguments -join ' '))
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw ("Python command failed with exit code {0}" -f $LASTEXITCODE)
    }
}

Push-Location $Root
try {
    Invoke-Python -Arguments @('validator/validate.py', 'cases.xlsx')
    Invoke-Python -Arguments @('-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py', '-v')
    Invoke-Python -Arguments @('validator/make_report.py', 'cases.xlsx', $Report)
    $Profile = if ($Submission) { 'submission' } else { 'repo' }
    Invoke-Python -Arguments @('tools/preflight_submission.py', '--profile', $Profile)
    if ($FullRebuild) {
        Invoke-Python -Arguments @('tools/verify_rebuild.py', '--regenerate')
    } else {
        Invoke-Python -Arguments @('tools/verify_rebuild.py')
    }
    Write-Host 'PASS: all selected checks completed.' -ForegroundColor Green
}
finally {
    Pop-Location
    if (Test-Path $Report) { Remove-Item -LiteralPath $Report -Force }
}
