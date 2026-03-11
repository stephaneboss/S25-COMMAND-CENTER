param(
  [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$doctor = python "$repo\scripts\manage_secrets.py" doctor
Write-Host $doctor
if ($LASTEXITCODE -ne 0) {
  throw "Secret doctor failed"
}

$renderArgs = @(
  "$repo\scripts\render_cockpit_manifest.py"
)

if ($OutputPath) {
  $renderArgs += @("--output", $OutputPath)
}

$rendered = python @renderArgs
if ($LASTEXITCODE -ne 0) {
  throw "Cockpit manifest rendering failed"
}
Write-Host ""
Write-Host "Rendered manifest:"
Write-Host $rendered
Write-Host ""
Write-Host "Next:"
Write-Host "1. Open Akash New Deployment"
Write-Host "2. Upload the rendered manifest"
Write-Host "3. Review pricing and deploy"
Write-Host "4. Sign only when Keplr prompts"
