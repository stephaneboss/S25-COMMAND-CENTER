#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import tempfile
from pathlib import Path

import cosmospy
import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.google_secret_runtime import access_secret, build_client, materialize_adc_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a public-safe S25 master wallet status snapshot")
    parser.add_argument("--project-id", default=os.getenv("GOOGLE_CLOUD_PROJECT", ""))
    parser.add_argument("--secret-id", default="s25-master-seed")
    parser.add_argument("--s25-url", default="https://s25.smajor.org")
    parser.add_argument("--hrp", default="akash")
    parser.add_argument("--adc-path", default=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/google-adc.json"))
    parser.add_argument("--format", choices=("summary", "json", "html"), default="summary")
    parser.add_argument("--output", default="")
    return parser


def derive_wallet_address(seed_phrase: str, hrp: str) -> str:
    privkey = cosmospy.seed_to_privkey(seed_phrase, path="m/44'/118'/0'/0/0")
    return cosmospy.privkey_to_address(privkey, hrp=hrp)


def fetch_s25_status(base_url: str) -> dict:
    status = {}
    errors = []
    for path in ("/api/status", "/api/version"):
        try:
            response = requests.get(base_url.rstrip("/") + path, timeout=15)
            response.raise_for_status()
            payload = response.json()
            if path.endswith("/status"):
                status["status"] = payload
            else:
                status["version"] = payload
        except Exception as exc:
            errors.append(f"{path}:{exc}")
    if errors:
        status["errors"] = errors
    return status


def build_payload(args: argparse.Namespace) -> dict:
    adc_ready, adc_detail = materialize_adc_file(Path(args.adc_path))
    if adc_ready:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = adc_detail

    client = build_client()
    seed_phrase = access_secret(client, args.project_id, args.secret_id)
    wallet_address = derive_wallet_address(seed_phrase, args.hrp)
    s25 = fetch_s25_status(args.s25_url)
    status = s25.get("status", {})
    version = s25.get("version", {})
    return {
        "ok": True,
        "project_id": args.project_id,
        "secret_id": args.secret_id,
        "wallet_address": wallet_address,
        "wallet_prefix": args.hrp,
        "s25_url": args.s25_url,
        "s25_connection": {
            "pipeline_status": status.get("pipeline_status", "unknown"),
            "mesh_agents_online": status.get("mesh_agents_online"),
            "missions_active": status.get("missions_active"),
            "arkon5_action": status.get("arkon5_action"),
            "build_sha": version.get("build_sha"),
            "errors": s25.get("errors", []),
        },
    }


def render_html(payload: dict) -> str:
    conn = payload["s25_connection"]
    wallet = html.escape(payload["wallet_address"])
    pipeline = html.escape(str(conn.get("pipeline_status", "unknown")))
    build_sha = html.escape(str(conn.get("build_sha", "--")))
    missions = html.escape(str(conn.get("missions_active", "--")))
    agents = html.escape(str(conn.get("mesh_agents_online", "--")))
    action = html.escape(str(conn.get("arkon5_action", "--")))
    errors = conn.get("errors", [])
    error_html = (
        "<ul>" + "".join(f"<li>{html.escape(err)}</li>" for err in errors) + "</ul>"
        if errors
        else "<p>No upstream errors reported.</p>"
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>S25 Master Wallet Status</title>
    <style>
      body {{
        margin: 0;
        font-family: Consolas, monospace;
        background: #05080d;
        color: #e6fff7;
      }}
      main {{
        max-width: 1080px;
        margin: 0 auto;
        padding: 40px 20px 80px;
      }}
      .panel {{
        border: 1px solid rgba(124,246,212,0.22);
        border-radius: 28px;
        padding: 24px;
        background: linear-gradient(180deg, rgba(7,24,21,0.92) 0%, rgba(4,10,11,0.96) 100%);
        box-shadow: 0 0 40px rgba(124,246,212,0.09);
      }}
      .eyebrow {{
        color: #7cf6d4;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-size: 12px;
      }}
      h1 {{
        margin: 12px 0 8px;
        font-size: 42px;
      }}
      .wallet {{
        font-size: 24px;
        color: #7cf6d4;
        word-break: break-all;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
        margin-top: 18px;
      }}
      .metric {{
        border: 1px solid rgba(124,246,212,0.14);
        border-radius: 18px;
        padding: 14px;
        background: rgba(255,255,255,0.03);
      }}
      .metric span {{
        display: block;
        color: #8eb7ad;
        font-size: 12px;
        text-transform: uppercase;
        margin-bottom: 8px;
      }}
      .metric strong {{
        font-size: 26px;
      }}
      .subpanel {{
        margin-top: 18px;
        border: 1px solid rgba(124,246,212,0.14);
        border-radius: 18px;
        padding: 18px;
        background: rgba(255,255,255,0.03);
      }}
      @media (max-width: 900px) {{
        .grid {{ grid-template-columns: 1fr 1fr; }}
      }}
      @media (max-width: 560px) {{
        .grid {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="panel">
        <div class="eyebrow">S25 Master Wallet</div>
        <h1>Wallet creator public status</h1>
        <p>Public address only. Seed phrase never exposed.</p>
        <div class="wallet">{wallet}</div>
        <div class="grid">
          <div class="metric"><span>Pipeline</span><strong>{pipeline}</strong></div>
          <div class="metric"><span>Agents online</span><strong>{agents}</strong></div>
          <div class="metric"><span>Missions</span><strong>{missions}</strong></div>
          <div class="metric"><span>Signal</span><strong>{action}</strong></div>
        </div>
        <div class="subpanel">
          <strong>Build</strong>
          <p>{build_sha}</p>
        </div>
        <div class="subpanel">
          <strong>Runtime errors</strong>
          {error_html}
        </div>
      </section>
    </main>
  </body>
</html>
"""


def main() -> int:
    args = build_parser().parse_args()
    if not args.project_id:
        print(json.dumps({"ok": False, "error": "google_cloud_project_missing"}, indent=2))
        return 1

    payload = build_payload(args)

    if args.format == "summary":
        print(json.dumps(payload, indent=2))
        return 0

    if args.format == "json":
        rendered = json.dumps(payload, indent=2)
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered)
        return 0

    rendered = render_html(payload)
    output = Path(args.output) if args.output else Path(tempfile.gettempdir()) / "s25-master-wallet-status.html"
    output.write_text(rendered, encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "wallet_address": payload["wallet_address"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
