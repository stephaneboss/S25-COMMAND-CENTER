$repo = "C:\Users\Steph\Documents\Playground\S25-COMMAND-CENTER-git"

Write-Host "[S25] project snapshot"
Write-Host ""

Write-Host "HEAD:"
git -C $repo rev-parse --short HEAD

Write-Host ""
Write-Host "Recent commits:"
git -C $repo log --oneline -5

Write-Host ""
Write-Host "Worktree:"
git -C $repo status --short

Write-Host ""
Write-Host "Key docs:"
@(
  "docs/WORKSTREAM_BOARD.md",
  "docs/CLAUDE_CODEX_HANDOFF.md",
  "docs/AKASH_AUTONOMY_TARGET.md",
  "docs/TRINITY_ACTIVATION_RUNBOOK.md",
  "docs/GEMINI_FOUNDATION.md"
) | ForEach-Object { Write-Host "- $_" }
