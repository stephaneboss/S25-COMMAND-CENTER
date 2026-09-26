#!/usr/bin/env python3
"""Push full system health + market data to HA sensors for dashboard."""
import os
from pathlib import Path

import requests


def load_ha_config():
    """Read both values regardless of their order in .env."""
    values = {}
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip() in ("HA_URL", "HA_TOKEN"):
                values[key.strip()] = value.strip().strip('"').strip("'")

    url = os.environ.get("HA_URL") or values.get("HA_URL")
    token = os.environ.get("HA_TOKEN") or values.get("HA_TOKEN")
    if not url or not token:
        raise SystemExit("HA_URL and HA_TOKEN must be configured")
    return url.rstrip("/"), token


HA, TOKEN = load_ha_config()
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def push(entity, state, attrs):
    r = requests.post(f"{HA}/api/states/{entity}", headers=H, json={
        "state": str(state), "attributes": attrs
    }, timeout=10)
    r.raise_for_status()
    print(f"  {entity} = {state} -> {r.status_code}")

# Get system health from cockpit
try:
    health = requests.get("http://localhost:7777/api/system/health", timeout=10).json()
except Exception as e:
    print(f"Cannot get health: {e}")
    health = {}

# Get market data
try:
    market = requests.get("http://localhost:7777/api/market/live", timeout=15).json()
except Exception as e:
    print(f"Cannot get market: {e}")
    market = {}

# Push system health sensors
if health:
    # GPU
    gpu = health.get("gpu", {})
    if gpu.get("temp_c"):
        push("sensor.s25_gpu_temp", gpu["temp_c"], {
            "friendly_name": "S25 GPU Temperature",
            "unit_of_measurement": "°C",
            "vram_used_mb": gpu.get("vram_used_mb"),
            "vram_total_mb": gpu.get("vram_total_mb"),
            "utilization_pct": gpu.get("utilization_pct"),
            "icon": "mdi:expansion-card",
        })

    # Disk
    disk = health.get("disk", {})
    if disk.get("pct"):
        push("sensor.s25_disk_usage", disk["pct"], {
            "friendly_name": "S25 Disk Usage",
            "total": disk.get("total"),
            "used": disk.get("used"),
            "available": disk.get("avail"),
            "icon": "mdi:harddisk",
        })

    # Cockpit uptime
    cockpit = health.get("cockpit", {})
    if cockpit.get("uptime_s"):
        hours = cockpit["uptime_s"] // 3600
        mins = (cockpit["uptime_s"] % 3600) // 60
        push("sensor.s25_cockpit_uptime", f"{hours}h{mins}m", {
            "friendly_name": "S25 Cockpit Uptime",
            "uptime_seconds": cockpit["uptime_s"],
            "pid": cockpit.get("pid"),
            "icon": "mdi:clock-outline",
        })

    # Docker containers
    docker = health.get("docker", {})
    running = len([v for v in docker.values() if "Up" in str(v)])
    push("sensor.s25_docker_containers", f"{running}/{len(docker)}", {
        "friendly_name": "S25 Docker Containers",
        "containers": docker,
        "icon": "mdi:docker",
    })

    # Ollama
    ollama = health.get("ollama", {})
    push("sensor.s25_ollama_status", ollama.get("status", "unknown"), {
        "friendly_name": "S25 Ollama LLM",
        "models": ollama.get("models", []),
        "icon": "mdi:brain",
    })

    # Cloudflare
    cf = health.get("cloudflare", {})
    push("sensor.s25_cloudflare_status", cf.get("tunnels", "unknown"), {
        "friendly_name": "S25 Cloudflare Tunnels",
        "pids": cf.get("pids", []),
        "icon": "mdi:cloud-check",
    })

# Push market data sensors
if market:
    prices = market.get("prices", {})
    for coin, data in prices.items():
        symbol = {
            "bitcoin": "BTC", "ethereum": "ETH", "dogecoin": "DOGE",
            "solana": "SOL", "cosmos": "ATOM", "akash-network": "AKT",
            "chainlink": "LINK", "uniswap": "UNI", "aave": "AAVE", "maker": "MKR",
        }.get(coin, coin.upper()[:4])
        push(f"sensor.s25_price_{symbol.lower()}", round(data["usd"], 2), {
            "friendly_name": f"S25 {symbol} Price",
            "unit_of_measurement": "USD",
            "change_24h": data.get("change_24h", 0),
            "icon": "mdi:currency-usd",
        })

    # Global market
    gm = market.get("global", {})
    if gm:
        cap_t = round(gm.get("total_market_cap_usd", 0) / 1e12, 2)
        push("sensor.s25_market_cap", f"{cap_t}T", {
            "friendly_name": "S25 Crypto Market Cap",
            "total_usd": gm.get("total_market_cap_usd"),
            "btc_dominance": gm.get("btc_dominance"),
            "eth_dominance": gm.get("eth_dominance"),
            "icon": "mdi:chart-line",
        })

    # Trending
    trending = market.get("trending", [])
    if trending:
        top3 = ", ".join(t["symbol"] for t in trending[:3])
        push("sensor.s25_trending", top3, {
            "friendly_name": "S25 Trending Crypto",
            "top_10": [{"name": t["name"], "symbol": t["symbol"]} for t in trending[:10]],
            "icon": "mdi:trending-up",
        })

print("\nAll sensors pushed to HA!")
