param(
    [string]$BaseUrl = "https://trinity-s25-proxy.trinitys25steph.workers.dev",
    [string]$Token = "",
    [string]$Priority = "high"
)

if (-not $Token) {
    throw "Provide -Token with a contract or token address."
}

$payload = @{
    created_by = "TRINITY"
    target = "ONCHAIN_GUARDIAN"
    task_type = "infra_monitoring"
    intent = "Verifier le risque on-chain, LP, whales et rugpull pour $Token"
    priority = $Priority
    context = @{
        token = $Token
    }
} | ConvertTo-Json -Depth 6

Write-Host "[GUARDIAN] queue mission on $BaseUrl"
$mission = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/missions" -ContentType "application/json" -Body $payload
$missions = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/missions"

[PSCustomObject]@{
    mission_ok = $mission.ok
    mission_id = $mission.mission.mission_id
    target = $mission.mission.target
    token = $Token
    active_count = $missions.active.Count
} | Format-List
