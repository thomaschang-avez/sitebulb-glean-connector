"""
main.py — SITEBULB ZOS
Full pipeline entry point. Parse → Diff → Slack → Glean. One command.

Usage:
  python3 main.py                    # Full run (all 20 clients)
  python3 main.py --dry-run          # Validate config only
  python3 main.py --skip-glean       # Skip Glean push
  python3 main.py --skip-slack       # Skip Slack alerts
"""

import os
import sys
import json
import argparse
import traceback
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

REQUIRED_ENV_VARS = [
    "GLEAN_INDEXING_API_TOKEN",
    "GLEAN_SERVER_URL",
    "GLEAN_INSTANCE",
    "SLACK_BOT_TOKEN",
    "GOOGLE_SHEETS_ID",
]


# ─────────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────────

def validate_env() -> bool:
    missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        print(f"❌ Missing env vars: {', '.join(missing)}")
        print("   Check your .env file.")
        return False
    return True


# ─────────────────────────────────────────────────────────────────
# DRY RUN
# ─────────────────────────────────────────────────────────────────

def dry_run():
    from config import CLIENTS, HINT_MAPPING, USE_TEST_CHANNEL, TEST_CHANNEL
    print("\n" + "=" * 60)
    print("  SITEBULB ZOS — DRY RUN")
    print("=" * 60)
    print(f"\n  {len(CLIENTS)} clients configured:")
    for c in CLIENTS:
        print(f"    {c['name']:<35} {c['url']}")
    print(f"\n  {len(HINT_MAPPING)} hints mapped")
    print(f"  Mode: {'TEST → ' + TEST_CHANNEL if USE_TEST_CHANNEL else 'PRODUCTION'}")
    print(f"\n  Output directory: output/")
    snapshots = list(Path("output").glob("*_latest.json")) if Path("output").exists() else []
    print(f"  Existing snapshots: {len(snapshots)}")
    for s in sorted(snapshots):
        print(f"    {s.name}")
    print()


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  AVENUE Z — SITEBULB ZOS PIPELINE")
    print("=" * 60 + "\n")

    parser = argparse.ArgumentParser(description="Sitebulb ZOS Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Validate config only")
    parser.add_argument("--skip-glean", action="store_true", help="Skip Glean push")
    parser.add_argument("--skip-slack", action="store_true", help="Skip Slack alerts")
    args = parser.parse_args()

    if not validate_env():
        sys.exit(1)

    if args.dry_run:
        dry_run()
        return

    # ── STEP 1: Parse all clients from Google Sheets ──
    print(f"  [1/4] Parsing Historical Hint Data from Google Sheets...")
    try:
        from parser import parse_all_clients
        snapshots = parse_all_clients()
        
        if not snapshots:
            print(f"  ⚠️  No audits found in Google Sheets")
            sys.exit(0)
        
        print(f"  ✅ Parsed {len(snapshots)} client audits")
    except Exception as e:
        print(f"  ❌ Parse failed: {e}")
        traceback.print_exc()
        sys.exit(1)

    # ── STEP 2: Process each client (diff + slack + glean) ──
    print(f"\n  [2/4] Processing {len(snapshots)} clients...\n")
    
    for snapshot in snapshots.values():
        client_name = snapshot['client']
        safe_name = client_name.replace(' ', '_').replace('&', 'and').replace('/', '_')
        
        print(f"  → {client_name}")
        
        try:
            # ── Diff vs previous snapshot ──
            from diff import find_snapshots, load_snapshot, diff_snapshots, save_diff
            
            all_snapshots = find_snapshots(safe_name)
            
            if len(all_snapshots) >= 2:
                print(f"    Diffing vs previous snapshot...")
                prev_snapshot = load_snapshot(all_snapshots[-2])
                current_snapshot = load_snapshot(all_snapshots[-1])
                diff_result = diff_snapshots(prev_snapshot, current_snapshot)
                diff_path = save_diff(diff_result, safe_name)
                print(f"    Saved diff: {diff_path}")
            else:
                print(f"    First run — no previous snapshot")
                diff_result = None
            
            # ── Slack alert ──
            if not args.skip_slack:
                from slack_alert import send_alert
                
                if diff_result:
                    send_alert(safe_name, diff=diff_result)
                    print(f"    Slack: Diff alert sent")
                else:
                    send_alert(safe_name, snapshot=snapshot)
                    print(f"    Slack: First-run alert sent")
            else:
                print(f"    Slack: Skipped (--skip-slack)")
            
            # ── Glean push ──
            if not args.skip_glean:
                from glean_push import push_snapshot
                push_snapshot(snapshot)
                print(f"    Glean: Pushed to sitebulbaudits")
            else:
                print(f"    Glean: Skipped (--skip-glean)")
            
            print()
            
        except Exception as e:
            print(f"    ❌ Error processing {client_name}: {e}")
            traceback.print_exc()
            print()
            continue

    print(f"  [3/4] Saving snapshots to output/...\n")
    # Snapshots already saved by parser.py — just confirm
    output_dir = Path("output")
    latest_files = list(output_dir.glob("*_latest.json"))
    print(f"  ✅ {len(latest_files)} snapshots in output/")
    
    print(f"\n  [4/4] Pipeline complete.\n")
    print("  Next commands:")
    print(f"    Full run:     python3 main.py")
    print(f"    Dry run:      python3 main.py --dry-run")
    print(f"    Skip Glean:   python3 main.py --skip-glean")
    print(f"    Skip Slack:   python3 main.py --skip-slack")
    print()


if __name__ == "__main__":
    main()
