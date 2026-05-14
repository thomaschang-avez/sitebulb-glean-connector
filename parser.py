"""
Sitebulb Historical Hint Data Parser
Reads per-client Google Sheets exports, scores issues, saves JSON snapshots
"""

import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from pathlib import Path
import config

def authenticate_gspread():
    creds = Credentials.from_service_account_file(
        config.GOOGLE_CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    return gspread.authorize(creds)

def read_client_sheet(gspread_client, sheet_id):
    """Read Historical Hint Data from a single client's sheet"""
    sheet = gspread_client.open_by_key(sheet_id)
    worksheet = sheet.get_worksheet(0)
    data = worksheet.get_all_values()
    if len(data) < 2:
        return None, None
    headers = data[0]
    rows = data[1:]
    return headers, rows

def get_latest_row(rows, date_col_idx):
    """Return the most recent row based on audit date"""
    latest_row = None
    latest_date = None
    for row in rows:
        if len(row) <= date_col_idx:
            continue
        date_str = row[date_col_idx].strip()
        try:
            audit_date = datetime.strptime(date_str, "%B %d, %Y")
        except ValueError:
            try:
                audit_date = datetime.strptime(date_str, "%b %d, %Y")
            except ValueError:
                continue
        if latest_date is None or audit_date > latest_date:
            latest_date = audit_date
            latest_row = row
    return latest_row, latest_date

def score_hints(headers, row):
    scores = {
        'critical': [],
        'high': [],
        'medium': [],
        'low': [],
        'total_score': 0
    }
    for i, header in enumerate(headers):
        if i < 3:
            continue
        if i >= len(row):
            continue
        hint_name = header.strip()
        hint_count = row[i].strip()
        if hint_name not in config.HINT_MAPPING:
            continue
        try:
            count = int(hint_count)
        except ValueError:
            continue
        if count == 0:
            continue
        hint_config = config.HINT_MAPPING[hint_name]
        severity = hint_config['severity']
        category = hint_config['category']
        base_score = config.SEVERITY_SCORES[severity]
        total_score = base_score * count
        scores['total_score'] += total_score
        scores[severity].append({
            'hint': hint_name,
            'count': count,
            'category': category,
            'base_score': base_score,
            'total_score': total_score
        })
    return scores

def save_snapshot(client_name, audit_date, scores):
    Path(config.OUTPUT_DIR).mkdir(exist_ok=True)
    safe_name = client_name.replace(' ', '_').replace('&', 'and').replace('/', '_')
    snapshot = {
        'client': client_name,
        'audit_date': audit_date.strftime("%Y-%m-%d"),
        'audit_date_formatted': audit_date.strftime("%B %d, %Y"),
        'total_score': scores['total_score'],
        'critical_count': sum(h['count'] for h in scores['critical']),
        'high_count': sum(h['count'] for h in scores['high']),
        'medium_count': sum(h['count'] for h in scores['medium']),
        'low_count': sum(h['count'] for h in scores['low']),
        'critical_issues': scores['critical'],
        'high_issues': scores['high'],
        'medium_issues': scores['medium'],
        'low_issues': scores['low'],
        'timestamp': datetime.now().isoformat()
    }
    latest_path = Path(config.OUTPUT_DIR) / config.SNAPSHOT_FILENAME.format(client_name=safe_name)
    with open(latest_path, 'w') as f:
        json.dump(snapshot, f, indent=2)
    return snapshot

def parse_all_clients():
    print("Authenticating with Google Sheets...")
    gspread_client = authenticate_gspread()
    snapshots = {}

    for client in config.CLIENTS:
        client_name = client['name']
        sheet_id = client.get('sheet_id')

        if not sheet_id:
            print(f"  ⚠️  No sheet_id for {client_name} — skipping")
            continue

        print(f"\nProcessing: {client_name}")

        try:
            headers, rows = read_client_sheet(gspread_client, sheet_id)
            if headers is None:
                print(f"  ⚠️  Empty sheet — skipping")
                continue

            date_col_idx = headers.index('Audit Date')
            latest_row, audit_date = get_latest_row(rows, date_col_idx)

            if latest_row is None:
                print(f"  ⚠️  No valid audit rows — skipping")
                continue

            print(f"  Audit Date: {audit_date.strftime('%B %d, %Y')}")
            scores = score_hints(headers, latest_row)
            print(f"  Total Score: {scores['total_score']}")
            print(f"  Critical: {sum(h['count'] for h in scores['critical'])}")
            print(f"  High: {sum(h['count'] for h in scores['high'])}")
            print(f"  Medium: {sum(h['count'] for h in scores['medium'])}")
            print(f"  Low: {sum(h['count'] for h in scores['low'])}")

            snapshot = save_snapshot(client_name, audit_date, scores)
            snapshots[client_name] = snapshot

        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

    print(f"\n✅ Parsed {len(snapshots)} client audits")
    return snapshots

if __name__ == '__main__':
    parse_all_clients()
