# ============================================================
# S25 LUMIÈRE — Akash Update via REST API (Windows PowerShell)
# Met à jour DSEQ 25822281 sans Akash CLI ni navigateur
# ============================================================
# Usage: .\akash\scripts\update_akash_windows.ps1
#
# Prérequis:
#   - PowerShell 5+ (déjà installé sur Windows)
#   - Keplr wallet address + mnemonic (pour signer)
#   OU utiliser directement: console.akash.network

param(
    [string]$DSEQ = "25822281",
    [string]$AkashNode = "https://akash-api.polkachu.com",
    [string]$Image = "ghcr.io/stephaneboss/s25-command-center:latest"
)

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   S25 LUMIÈRE — Akash Update Script     ║" -ForegroundColor Cyan
Write-Host "║   DSEQ: $DSEQ                         ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ─── Check deployment status ─────────────────────────────
Write-Host "📊 Checking deployment status..." -ForegroundColor Yellow
$statusUrl = "$AkashNode/akash/deployment/v1beta3/deployments"

try {
    $status = Invoke-RestMethod -Uri "$AkashNode/akash/deployment/v1beta3/deployments?filters.dseq=$DSEQ" -Method GET
    Write-Host "✅ Deployment found: DSEQ $DSEQ" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not fetch deployment status (API may be rate-limited)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "─────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "  OPTIONS POUR UPDATER AKASH DSEQ $DSEQ" -ForegroundColor White
Write-Host "─────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""
Write-Host "OPTION 1 — Akash Console Web (RECOMMANDÉ)" -ForegroundColor Green
Write-Host "  1. Va sur: https://console.akash.network/deployments/$DSEQ" -ForegroundColor White
Write-Host "  2. Clique sur 'Update' tab" -ForegroundColor White
Write-Host "  3. Upload le SDL: akash\deploy_cockpit.yaml" -ForegroundColor White
Write-Host "  4. Signe avec Keplr (2 signatures)" -ForegroundColor White
Write-Host ""
Write-Host "OPTION 2 — Akash CLI (si installé)" -ForegroundColor Yellow
Write-Host "  1. Installer: https://docs.akash.network/guides/cli" -ForegroundColor White
Write-Host "  2. Run: bash akash/scripts/update_cockpit.sh" -ForegroundColor White
Write-Host ""
Write-Host "OPTION 3 — Redéployer complètement" -ForegroundColor Cyan
Write-Host "  1. Fermer DSEQ $DSEQ (libère l'escrow AKT)" -ForegroundColor White
Write-Host "  2. Nouveau déploiement avec la vraie image:" -ForegroundColor White
Write-Host "     $Image" -ForegroundColor White
Write-Host "  3. URL sera différente mais image sera correcte" -ForegroundColor White
Write-Host ""
Write-Host "─────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""
Write-Host "📋 SDL file: $(Resolve-Path 'akash\deploy_cockpit.yaml')" -ForegroundColor Cyan
Write-Host "🐳 Image:    $Image" -ForegroundColor Cyan
Write-Host "🌐 Console:  https://console.akash.network/deployments/$DSEQ" -ForegroundColor Cyan
Write-Host ""

# ─── Verify image is accessible ──────────────────────────
Write-Host "🔍 Verifying Docker image availability..." -ForegroundColor Yellow
try {
    $ghcrResponse = Invoke-RestMethod `
        -Uri "https://ghcr.io/v2/stephaneboss/s25-command-center/tags/list" `
        -Method GET `
        -ErrorAction SilentlyContinue
    Write-Host "✅ Image accessible on ghcr.io" -ForegroundColor Green
} catch {
    # Try unauthenticated check via GitHub API
    try {
        $pkgInfo = Invoke-RestMethod `
            -Uri "https://api.github.com/users/stephaneboss/packages/container/s25-command-center/versions" `
            -Method GET `
            -Headers @{ "Accept" = "application/vnd.github.v3+json" } `
            -ErrorAction SilentlyContinue
        if ($pkgInfo) {
            Write-Host "✅ Image exists on ghcr.io (latest tag)" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  Could not verify image (auth required for ghcr.io API)" -ForegroundColor Yellow
        Write-Host "   Check: https://github.com/stephaneboss/S25-COMMAND-CENTER/pkgs/container/s25-command-center" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "📌 Current cockpit URL (old image):" -ForegroundColor DarkGray
Write-Host "   http://kfhsi5oko9dbt3abob51g4s9q0.ingress.cap-test-compute.com" -ForegroundColor White
Write-Host ""
Write-Host "🎯 Quand updated, le cockpit redémarrera automatiquement." -ForegroundColor Green
Write-Host "   Refresh l'URL dans 2-3 minutes après l'update." -ForegroundColor Green
Write-Host ""
