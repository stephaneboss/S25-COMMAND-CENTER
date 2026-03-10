param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)

python "scripts/manage_secrets.py" @ArgsList
