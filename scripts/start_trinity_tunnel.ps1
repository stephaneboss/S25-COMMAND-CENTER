param(
    [string]$CloudflaredPath = "C:\Program Files (x86)\cloudflared\cloudflared.exe",
    [string]$OriginUrl = "http://kfhsi5oko9dbt3abob51g4s9q0.ingress.cap-test-compute.com",
    [string]$OriginHostHeader = "kfhsi5oko9dbt3abob51g4s9q0.ingress.cap-test-compute.com",
    [string]$LogFile = "C:\Users\Steph\Documents\Playground\cloudflared-trinity.log"
)

if (-not (Test-Path $CloudflaredPath)) {
    throw "cloudflared introuvable: $CloudflaredPath"
}

$cmd = @(
    "tunnel",
    "--url", $OriginUrl,
    "--http-host-header", $OriginHostHeader,
    "--logfile", $LogFile
)

Write-Host "[TRINITY] starting quick tunnel"
Write-Host "[TRINITY] origin = $OriginUrl"
Write-Host "[TRINITY] host header = $OriginHostHeader"
Write-Host "[TRINITY] logfile = $LogFile"

& $CloudflaredPath @cmd
