#!/bin/bash
# ============================================================
# S25 LUMIÈRE — Update Akash Deployment Script
# Met à jour DSEQ 25822281 avec la nouvelle image Docker
# ============================================================
# Usage: bash akash/scripts/update_cockpit.sh
#
# Prérequis:
#   - Akash CLI installé: curl -sSfL https://raw.githubusercontent.com/akash-network/node/master/install.sh | sh
#   - Wallet Akash configuré: akash keys add s25-wallet --recover
#   - AKT disponible pour gas

set -e

DSEQ="25822281"
WALLET_NAME="${AKASH_WALLET_NAME:-s25-wallet}"
CHAIN_ID="akashnet-2"
NODE="https://rpc.akash.forbole.com:443"
SDL_FILE="akash/deploy_cockpit.yaml"

echo "================================================"
echo "  S25 LUMIÈRE — Akash Deployment Update"
echo "  DSEQ: $DSEQ"
echo "  Image: ghcr.io/stephaneboss/s25-command-center:latest"
echo "================================================"
echo ""

# Check akash CLI
if ! command -v akash &> /dev/null; then
    echo "❌ Akash CLI non trouvé!"
    echo "   Installer: curl -sSfL https://raw.githubusercontent.com/akash-network/node/master/install.sh | sh"
    exit 1
fi

echo "✅ Akash CLI: $(akash version)"
echo ""

# Check SDL exists
if [ ! -f "$SDL_FILE" ]; then
    echo "❌ SDL file not found: $SDL_FILE"
    exit 1
fi

echo "📋 SDL: $SDL_FILE"
echo ""
echo "🔄 Updating deployment DSEQ $DSEQ..."
echo ""

# Update deployment
akash tx deployment update \
    "$SDL_FILE" \
    --dseq "$DSEQ" \
    --from "$WALLET_NAME" \
    --chain-id "$CHAIN_ID" \
    --node "$NODE" \
    --gas auto \
    --gas-adjustment 1.5 \
    --gas-prices "0.025uakt" \
    -y

echo ""
echo "✅ Deployment update submitted!"
echo "   Vérifier sur: https://console.akash.network/deployments/$DSEQ"
echo ""

# Wait for update to propagate
sleep 10

# Check status
echo "📊 Status du déploiement:"
akash query deployment get \
    --owner "$(akash keys show $WALLET_NAME -a)" \
    --dseq "$DSEQ" \
    --node "$NODE" \
    --output json | python3 -c "
import json, sys
d = json.load(sys.stdin)
dep = d.get('deployment', {})
state = dep.get('state', '?')
print(f'  State: {state}')
"

echo ""
echo "🎯 Done! Le cockpit redémarre avec la nouvelle image."
echo "   URL: http://kfhsi5oko9dbt3abob51g4s9q0.ingress.cap-test-compute.com"
