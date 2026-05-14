"""
diff.py — SITEBULB ZOS
Compares two Sitebulb audit snapshots (hint counts) month-over-month.

Usage:
  python3 diff.py --client Avenue_Z
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict


OUTPUT_DIR = Path("output")
SEVERITY_ORDER = ["critical", "high", "medium", "low"]
SEVERITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🔵",
}


# ─────────────────────────────────────────────────────────────────
# SNAPSHOT DISCOVERY
# ─────────────────────────────────────────────────────────────────

def find_snapshots(client: str) -> list:
    """Return all snapshot paths for a client, sorted oldest → newest."""
    # Match both latest and archived snapshots
    latest = OUTPUT_DIR / f"{client}_latest.json"
    archived = sorted(OUTPUT_DIR.glob(f"{client}_2*.json"))  # e.g. Avenue_Z_2026-05-08.json
    
    paths = []
    if archived:
        paths.extend(archived)
    if latest.exists():
        paths.append(latest)
    
    return paths


def load_snapshot(path: Path) -> dict:
    return json.loads(Path(path).read_text())


# ─────────────────────────────────────────────────────────────────
# DIFF LOGIC
# ─────────────────────────────────────────────────────────────────

def issues_by_key(snapshot: dict) -> dict:
    """Index all issues by hint name for comparison."""
    index = {}
    for severity in SEVERITY_ORDER:
        for issue in snapshot.get(f"{severity}_issues", []):
            index[issue["hint"]] = {
                "hint": issue["hint"],
                "severity": severity,
                "category": issue.get("category", ""),
                "count": issue["count"],
                "total_score": issue["total_score"],
            }
    return index


def diff_snapshots(old: dict, new: dict) -> dict:
    old_index = issues_by_key(old)
    new_index = issues_by_key(new)

    old_hints = set(old_index.keys())
    new_hints = set(new_index.keys())

    fixed_hints   = old_hints - new_hints        # gone in new
    introduced_hints = new_hints - old_hints     # new in new
    persisted_hints  = old_hints & new_hints     # in both

    # Score delta per severity for fixed/introduced
    def severity_counts(hints, index):
        counts = defaultdict(int)
        for h in hints:
            counts[index[h]["severity"]] += 1
        return dict(counts)

    # Count delta for persisted (count changes)
    worsened = []
    improved = []
    for hint in persisted_hints:
        old_count = old_index[hint]["count"]
        new_count = new_index[hint]["count"]
        if new_count > old_count:
            worsened.append({**new_index[hint], "delta": new_count - old_count})
        elif new_count < old_count:
            improved.append({**new_index[hint], "delta": old_count - new_count})

    return {
        "client": new.get("client", ""),
        "old_date": old.get("audit_date", ""),
        "new_date": new.get("audit_date", ""),
        "old_score": old.get("total_score", 0),
        "new_score": new.get("total_score", 0),
        "old_total": len(old_hints),
        "new_total": len(new_hints),
        "fixed_count": len(fixed_hints),
        "introduced_count": len(introduced_hints),
        "persisted_count": len(persisted_hints),
        "fixed_by_severity": severity_counts(fixed_hints, old_index),
        "introduced_by_severity": severity_counts(introduced_hints, new_index),
        "fixed_issues": [old_index[h] for h in sorted(fixed_hints)],
        "introduced_issues": [new_index[h] for h in sorted(introduced_hints)],
        "worsened_issues": sorted(worsened, key=lambda x: x["total_score"], reverse=True),
        "improved_issues": sorted(improved, key=lambda x: x["delta"], reverse=True),
    }


def save_diff(diff: dict, client: str):
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / f"{client}_diff.json"
    path.write_text(json.dumps(diff, indent=2))
    return path


# ─────────────────────────────────────────────────────────────────
# PRINT REPORT
# ─────────────────────────────────────────────────────────────────

def print_diff_report(diff: dict):
    client = diff["client"].upper()
    score_delta = diff["new_score"] - diff["old_score"]
    delta_str = f"+{score_delta}" if score_delta > 0 else str(score_delta)

    print()
    print("=" * 60)
    print(f"  {client} — AUDIT DIFF")
    print(f"  {diff['old_date']}  →  {diff['new_date']}")
    print("=" * 60)
    print(f"  Score:  {diff['old_score']} → {diff['new_score']} ({delta_str})")
    print(f"  Hints:  {diff['old_total']} → {diff['new_total']}")
    print(f"  ✅ Fixed: {diff['fixed_count']}  🔴 New: {diff['introduced_count']}  ⏳ Persisted: {diff['persisted_count']}")

    if diff["introduced_issues"]:
        print(f"\n  New Issues:")
        for i in diff["introduced_issues"][:5]:
            emoji = SEVERITY_EMOJI.get(i["severity"], "•")
            print(f"    {emoji} {i['hint']} ({i['count']} URLs)")

    if diff["worsened_issues"]:
        print(f"\n  Worsened:")
        for i in diff["worsened_issues"][:5]:
            print(f"    🔺 {i['hint']} (+{i['delta']} URLs)")
    print()


# ─────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Diff two Sitebulb snapshots")
    parser.add_argument("--client", required=True, help="Client slug (e.g. Avenue_Z)")
    args = parser.parse_args()

    snapshots = find_snapshots(args.client)
    if len(snapshots) < 2:
        print(f"⚠️  Need 2+ snapshots to diff. Found: {len(snapshots)}")
        return

    old = load_snapshot(snapshots[-2])
    new = load_snapshot(snapshots[-1])
    diff = diff_snapshots(old, new)
    print_diff_report(diff)
    path = save_diff(diff, args.client)
    print(f"Diff saved: {path}")


if __name__ == "__main__":
    main()
