param(
    [string]$BaseUrl = "https://trinity-s25-proxy.trinitys25steph.workers.dev",
    [string]$Symbol = "BTC",
    [string]$Priority = "high"
)

$payload = @{
    created_by = "TRINITY"
    target = "ORACLE"
    task_type = "infra_monitoring"
    intent = "Valider le prix multi-source de $Symbol et detecter toute derive oracle"
    priority = $Priority
    context = @{
        symbol = $Symbol
    }
} | ConvertTo-Json -Depth 6

Write-Host "[ORACLE] queue mission on $BaseUrl"
$mission = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/missions" -ContentType "application/json" -Body $payload
$missions = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/missions"

[PSCustomObject]@{
    mission_ok = $mission.ok
    mission_id = $mission.mission.mission_id
    target = $mission.mission.target
    symbol = $Symbol
    active_count = $missions.active.Count
} | Format-List
