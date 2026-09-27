"""Fail CI on new flake8 findings while tracking existing repository debt."""

import argparse
import collections
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / ".github" / "flake8-baseline.json"
FINDING = re.compile(r"^(.+?):(\d+):(\d+): ([A-Z]\d+) (.+)$")
FLAKE8_ARGS = [
    sys.executable, "-m", "flake8", "agents/", "security/", "monitoring/",
    "--max-line-length=120",
    "--ignore=E501,W503,E302,E303,E221,E241,W504,E401,E701,E128,E226",
    "--exclude=__pycache__",
]


def findings(root):
    result = subprocess.run(FLAKE8_ARGS, cwd=root, text=True, capture_output=True)
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr or result.stdout)
    counts = collections.Counter()
    for entry in result.stdout.splitlines():
        match = FINDING.match(entry)
        if not match:
            raise RuntimeError(f"Unrecognized flake8 output: {entry}")
        path, row, _column, code, message = match.groups()
        source = (root / path).read_text(encoding="utf-8").splitlines()
        signature = (path, code, message, source[int(row) - 1].strip())
        counts[signature] += 1
    return counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate-from", type=Path, help="Write baseline from this checkout")
    args = parser.parse_args()
    if args.generate_from:
        counts = findings(args.generate_from.resolve())
        entries = [list(signature) + [count] for signature, count in sorted(counts.items())]
        BASELINE.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
        print(f"Recorded {sum(counts.values())} existing findings")
        return

    baseline = collections.Counter({tuple(row[:4]): row[4] for row in json.loads(
        BASELINE.read_text(encoding="utf-8"))})
    current = findings(ROOT)
    added = current - baseline
    resolved = baseline - current
    print(f"flake8: {sum(current.values())} findings, "
          f"{sum(resolved.values())} resolved, {sum(added.values())} new")
    for signature, count in sorted(added.items()):
        print(f"NEW {count}x {signature[0]} {signature[1]} {signature[2]}: {signature[3]}")
    if added:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
