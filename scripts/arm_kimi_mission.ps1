param(
    [string]$BaseUrl = "https://trinity-s25-proxy.trinitys25steph.workers.dev",
    [string]$Intent = "Scanner les memecoins, wallets whales et rugpull risks puis remonter les alerts Web3 prioritaires",
    [string]$Priority = "high"
)

$payload = @{
    created_by = "TRINITY"
    target = "KIMI"
    task_type = "market_news"
    intent = $Intent
    priority = $Priority
    context = @{
        cadence = "continuous"
        topics = @("memecoins", "whales", "rugpull", "solana", "ethereum", "base")
    }
} | ConvertTo-Json -Depth 6

Write-Host "[KIMI] queue mission on $BaseUrl"
$mission = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/missions" -ContentType "application/json" -Body $payload
$missions = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/missions"

[PSCustomObject]@{
    mission_ok = $mission.ok
    mission_id = $mission.mission.mission_id
    target = $mission.mission.target
    recommended_agent = $mission.mission.recommended_agent
    active_count = $missions.active.Count
    latest_target = if ($missions.active.Count -gt 0) { $missions.active[0].target } else { $null }
} | Format-List
