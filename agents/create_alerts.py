#!/usr/bin/env python3
"""
S25 Trading System - HA Alert Automations
Creates intelligent alert automations via HA REST API.
"""

import os
import requests

# Read HA token from .env
env_path = os.path.expanduser("~/S25-COMMAND-CENTER/.env")
ha_token = None
with open(env_path, "r") as f:
    for line in f:
        if line.startswith("HA_TOKEN="):
            ha_token = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
            break

if not ha_token:
    raise RuntimeError(f"HA_TOKEN not found in {env_path}")

HA_URL = "http://10.0.0.136:8123"
HEADERS = {
    "Authorization": f"Bearer {ha_token}",
    "Content-Type": "application/json",
}
NOTIFY_SERVICE = "notify.mobile_app_s_25"

automations = [
    {
        "id": "s25_alert_fear_greed",
        "alias": "S25 Alert - Extreme Fear Buying Opportunity",
        "description": "Triggers when Fear & Greed index drops below 15",
        "mode": "single",
        "triggers": [
            {
                "trigger": "numeric_state",
                "entity_id": "sensor.s25_fear_greed",
                "below": 15,
            }
        ],
        "conditions": [],
        "actions": [
            {
                "action": NOTIFY_SERVICE,
                "data": {
                    "title": "S25 EXTREME FEAR",
                    "message": "EXTREME FEAR - Buying opportunity (Fear & Greed: {{ states('sensor.s25_fear_greed') }})",
                },
            }
        ],
    },
    {
        "id": "s25_alert_gpu_overheat",
        "alias": "S25 Alert - GPU Overheating",
        "description": "Triggers when GPU temperature exceeds 85C",
        "mode": "single",
        "triggers": [
            {
                "trigger": "numeric_state",
                "entity_id": "sensor.s25_gpu_temp",
                "above": 85,
            }
        ],
        "conditions": [],
        "actions": [
            {
                "action": NOTIFY_SERVICE,
                "data": {
                    "title": "S25 GPU OVERHEAT",
                    "message": "GPU OVERHEATING - Check AlienStef (Temp: {{ states('sensor.s25_gpu_temp') }}C)",
                },
            }
        ],
    },
    {
        "id": "s25_alert_agent_down",
        "alias": "S25 Alert - Agent Down",
        "description": "Triggers when mesh agent count drops",
        "mode": "single",
        "triggers": [
            {
                "trigger": "state",
                "entity_id": "sensor.s25_mesh_online",
            }
        ],
        "conditions": [
            {
                "condition": "template",
                "value_template": "{{ trigger.to_state.state | int(0) < trigger.from_state.state | int(0) }}",
            }
        ],
        "actions": [
            {
                "action": NOTIFY_SERVICE,
                "data": {
                    "title": "S25 AGENT DOWN",
                    "message": "AGENT DOWN - Mesh count dropped to {{ states('sensor.s25_mesh_online') }} agents online",
                },
            }
        ],
    },
    {
        "id": "s25_alert_kill_switch",
        "alias": "S25 Alert - Kill Switch Activated",
        "description": "Triggers when kill switch is turned on",
        "mode": "single",
        "triggers": [
            {
                "trigger": "state",
                "entity_id": "input_boolean.s25_kill_switch",
                "to": "on",
            }
        ],
        "conditions": [],
        "actions": [
            {
                "action": NOTIFY_SERVICE,
                "data": {
                    "title": "S25 KILL SWITCH",
                    "message": "KILL SWITCH ON - Trading halted. All positions frozen.",
                },
            }
        ],
    },
    {
        "id": "s25_alert_btc_crash",
        "alias": "S25 Alert - BTC Crash",
        "description": "Triggers when BTC drops more than 5% in 24h",
        "mode": "single",
        "triggers": [
            {
                "trigger": "numeric_state",
                "entity_id": "sensor.s25_price_btc",
                "attribute": "change_24h",
                "below": -5,
            }
        ],
        "conditions": [],
        "actions": [
            {
                "action": NOTIFY_SERVICE,
                "data": {
                    "title": "S25 BTC CRASH",
                    "message": "BTC CRASH ALERT - 24h change: {{ state_attr('sensor.s25_price_btc', 'change_24h') }}% (Price: ${{ states('sensor.s25_price_btc') }})",
                },
            }
        ],
    },
]

print(f"Connecting to HA at {HA_URL}...")

# Verify connection
try:
    r = requests.get(f"{HA_URL}/api/", headers=HEADERS, timeout=10)
    r.raise_for_status()
    print(f"  Connected: {r.json().get('message', 'OK')}")
except Exception as e:
    print(f"  FAILED to connect: {e}")
    raise

# Create each automation
results = {"ok": [], "fail": []}
for auto in automations:
    auto_id = auto["id"]
    url = f"{HA_URL}/api/config/automation/config/{auto_id}"
    payload = {k: v for k, v in auto.items() if k != "id"}

    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=15)
        if r.status_code in (200, 201):
            print(f"  [OK] {auto['alias']}")
            results["ok"].append(auto_id)
        else:
            print(f"  [FAIL] {auto['alias']} -> {r.status_code}: {r.text}")
            results["fail"].append(auto_id)
    except Exception as e:
        print(f"  [FAIL] {auto['alias']} -> {e}")
        results["fail"].append(auto_id)

print(f"\nDone: {len(results['ok'])} created, {len(results['fail'])} failed")
if results["fail"]:
    print(f"Failed: {results['fail']}")
