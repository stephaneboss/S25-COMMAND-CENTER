param(
  [Parameter(Mandatory = $true)]
  [string]$Endpoint
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
python "$repo\scripts\test_merlin_mcp_handshake.py" $Endpoint
