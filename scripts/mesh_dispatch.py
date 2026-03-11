import argparse
import json
import sys
from pathlib import Path
from urllib import error, request


DEFAULT_ENDPOINT = "https://s25.smajor.org/api/missions"
DEFAULT_AGENTS = [
    "CODE_VALIDATOR",
    "SMART_REFACTOR",
]


def load_template(path: str) -> str:
    content = Path(path).read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"Template vide: {path}")
    return content


def build_payload(agent: str, action: str, template_body: str) -> dict:
    return {
        "target": agent,
        "task_type": "core_system_build",
        "priority": "critical",
        "created_by": "OMEGA_PROTOCOL",
        "intent": f"{action} via S25 OMEGA PROTOCOL",
        "context": {
            "protocol": "S25_OMEGA_PROTOCOL",
            "dispatch_mode": "broadcast",
            "assigned_agent": agent,
            "action": action,
            "template_body": template_body,
        },
    }


def post_payload(endpoint: str, secret: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "S25MeshDispatch/1.0",
            "X-S25-Secret": secret,
        },
    )
    with request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Broadcast a build directive to the S25 mesh.")
    parser.add_argument("--broadcast", action="store_true", help="Required flag for broadcast mode.")
    parser.add_argument("--template", required=True, help="Path to the template file.")
    parser.add_argument("--agents", default=",".join(DEFAULT_AGENTS), help="Comma-separated agent list.")
    parser.add_argument("--action", required=True, help="High-level action label.")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="S25 missions endpoint.")
    parser.add_argument("--secret", default="", help="S25 shared secret. Falls back to S25_SHARED_SECRET env if omitted.")
    args = parser.parse_args()

    if not args.broadcast:
        print("Refus: utilisez --broadcast pour envoyer au maillage.", file=sys.stderr)
        return 2

    secret = args.secret or ""
    if not secret:
        import os

        secret = os.environ.get("S25_SHARED_SECRET", "")
    if not secret:
        print("Refus: S25_SHARED_SECRET manquant.", file=sys.stderr)
        return 2

    template_body = load_template(args.template)
    agents = [agent.strip() for agent in args.agents.split(",") if agent.strip()]
    if not agents:
        print("Refus: aucun agent cible.", file=sys.stderr)
        return 2

    results = []
    for agent in agents:
        payload = build_payload(agent, args.action, template_body)
        try:
            response = post_payload(args.endpoint, secret, payload)
            results.append(
                {
                    "agent": agent,
                    "ok": response.get("ok", False),
                    "mission_id": response.get("mission", {}).get("mission_id"),
                    "recommended_agent": response.get("mission", {}).get("recommended_agent"),
                }
            )
        except error.HTTPError as exc:
            results.append({"agent": agent, "ok": False, "error": f"http_{exc.code}"})
        except Exception as exc:  # noqa: BLE001
            results.append({"agent": agent, "ok": False, "error": str(exc)})

    print(json.dumps({"ok": all(item.get("ok") for item in results), "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
