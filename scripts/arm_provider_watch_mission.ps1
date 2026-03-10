param(
    [string]$BaseUrl = "https://trinity-s25-proxy.trinitys25steph.workers.dev",
    [string]$Priority = "high"
)

$payload = @{
    created_by = "TRINITY"
    target = "COMET"
    task_type = "provider_watch"
    intent = "Monitor official product updates for OpenAI, Google Gemini, Anthropic, Perplexity Comet, and Akash. Return only primary-source changes, then map them to S25 impact and recommended action."
    priority = $Priority
    context = @{
        cadence = "daily"
        topics = @("openai", "gemini", "anthropic", "comet", "akash", "embeddings", "responses api", "shortcuts", "permissions")
        output_contract = @("provider", "source_url", "date_checked", "what_changed", "s25_impact", "recommended_action", "owner")
    }
} | ConvertTo-Json -Depth 6

Write-Host "[PROVIDER-WATCH] queue mission on $BaseUrl"
$mission = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/missions" -ContentType "application/json" -Body $payload
$missions = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/missions"

[PSCustomObject]@{
    mission_ok = $mission.ok
    mission_id = $mission.mission.mission_id
    target = $mission.mission.target
    task_type = $mission.mission.task_type
    active_mission_count = $missions.active.Count
} | Format-List
