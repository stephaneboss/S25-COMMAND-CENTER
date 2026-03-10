param(
    [Parameter(Mandatory = $true)]
    [string]$Query,
    [int]$TopK = 5
)

python -m agents.gemini_memory --query $Query --top-k $TopK
