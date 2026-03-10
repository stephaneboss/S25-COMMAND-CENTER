param(
    [string]$BaseUrl = "https://trinity-s25-proxy.trinitys25steph.workers.dev",
    [string]$Intent = "Scanner Akash, Cosmos, MEXC et memecoins 1m puis remonter les signaux critiques",
    [string]$Priority = "high"
)

$payload = @{
    created_by = "TRINITY"
    target = "COMET"
    task_type = "market_news"
    intent = $Intent
    priority = $Priority
    context = @{
        cadence = "continuous"
        topics = @("akash", "cosmos", "mexc", "memecoins", "rugpull", "whales")
    }
} | ConvertTo-Json -Depth 6

Write-Host "[COMET] queue mission on $BaseUrl"
$mission = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/missions" -ContentType "application/json" -Body $payload
$feed = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/comet/feed?n=5"

[PSCustomObject]@{
    mission_ok = $mission.ok
    mission_id = $mission.mission.mission_id
    target = $mission.mission.target
    recommended_agent = $mission.mission.recommended_agent
    comet_feed_count = $feed.count
    latest_feed_summary = if ($feed.feed.Count -gt 0) { $feed.feed[0].summary } else { $null }
} | Format-List
