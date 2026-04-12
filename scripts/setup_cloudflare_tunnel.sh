#!/bin/bash
# ============================================================
# S25 LUMIERE - Cloudflare Named Tunnel Setup
# Remplace les quick tunnels instables par un tunnel persistant
# A executer UNE SEULE FOIS sur AlienStef ou le serveur hote
# ============================================================
set -e

TUNNEL_NAME="s25-tunnel"
CONFIG_FILE="$(dirname "$0")/../cloudflare/tunnel-config.yml"
DOMAINS=("s25.smajor.org" "api.smajor.org" "merlin.smajor.org" "ollama.smajor.org")

echo "=== S25 Cloudflare Named Tunnel Setup ==="
echo ""

# 1. Verifier cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "[1/5] Installation de cloudflared..."
    curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i /tmp/cloudflared.deb
    rm /tmp/cloudflared.deb
else
    echo "[1/5] cloudflared deja installe: $(which cloudflared)"
fi

# 2. Authentification Cloudflare
echo "[2/5] Authentification Cloudflare (ouvre le navigateur)..."
cloudflared tunnel login

# 3. Creer le tunnel
echo "[3/5] Creation du tunnel '$TUNNEL_NAME'..."
cloudflared tunnel create "$TUNNEL_NAME"

# Recuperer l'ID du tunnel
TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
echo "    Tunnel ID: $TUNNEL_ID"

# 4. Router les DNS
echo "[4/5] Routage DNS..."
for domain in "${DOMAINS[@]}"; do
    echo "    $domain -> $TUNNEL_NAME"
    cloudflared tunnel route dns "$TUNNEL_NAME" "$domain" 2>/dev/null || echo "    (route existante pour $domain)"
done

# 5. Mettre a jour la config avec l'ID du tunnel
echo "[5/5] Mise a jour de la configuration..."
sed -i "s/TUNNEL_ID_ICI/$TUNNEL_ID/g" "$CONFIG_FILE"

echo ""
echo "=== Setup termine ==="
echo "Tunnel: $TUNNEL_NAME ($TUNNEL_ID)"
echo ""
echo "Pour lancer:"
echo "  cloudflared tunnel --config $CONFIG_FILE run $TUNNEL_NAME"
echo ""
echo "Pour installer en service systemd:"
echo "  sudo cloudflared service install --config $(realpath "$CONFIG_FILE")"
echo "  sudo systemctl enable cloudflared"
echo "  sudo systemctl start cloudflared"
