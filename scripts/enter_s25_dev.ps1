param([switch]$OpenEditor)
$ErrorActionPreference = 'Stop'
$repoPath = Split-Path -Parent $PSScriptRoot
Set-Location $repoPath
Write-Host "S25 Major dev : $repoPath"
git --no-optional-locks status --short
python -X utf8 "$PSScriptRoot\s25_dev_doctor.py"
if ($LASTEXITCODE -ne 0) { Write-Warning 'Une lecture du diagnostic a echoue.' }
if ($OpenEditor) { code.cmd $repoPath }
Write-Host 'Tests : .\.venv\Scripts\python.exe -X utf8 -m pytest -q tests/test_ha_control_evidence.py tests/test_mesh_status_view.py tests/test_mission_worker_noop.py'
Write-Host 'Ubuntu : wsl.exe -d Ubuntu'
