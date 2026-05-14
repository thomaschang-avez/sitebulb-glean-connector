"""
Sitebulb ZOS Configuration
Maps Sitebulb Historical Hint Data to X-Point SEO Framework
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# GOOGLE SHEETS CONFIGURATION
# ==============================================================================

GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'google-credentials.json')

# ==============================================================================
# GLEAN CONFIGURATION
# ==============================================================================

GLEAN_INSTANCE = os.getenv('GLEAN_INSTANCE', 'your-company')
GLEAN_SERVER_URL = os.getenv('GLEAN_SERVER_URL', 'https://your-company-be.glean.com')
GLEAN_API_TOKEN = os.getenv('GLEAN_API_TOKEN')
GLEAN_INDEXING_API_TOKEN = os.getenv('GLEAN_INDEXING_API_TOKEN')
GLEAN_DATASOURCE = 'sitebulbaudits'

# ==============================================================================
# SLACK CONFIGURATION
# ==============================================================================

SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
TEST_CHANNEL = os.getenv('TEST_CHANNEL', 'YOUR_TEST_CHANNEL_ID')
ERROR_CHANNEL = os.getenv('ERROR_CHANNEL', 'YOUR_ERROR_CHANNEL_ID')
USE_TEST_CHANNEL = os.getenv('USE_TEST_CHANNEL', 'True').lower() == 'true'

# ==============================================================================
# CLIENT CONFIGURATION — Each client needs its own Google Sheet with Sitebulb export
# ==============================================================================

# Add your clients here — each needs a Google Sheet with Sitebulb Historical Hint Data export
# sheet_id: the Google Sheets ID from the URL (docs.google.com/spreadsheets/d/SHEET_ID/edit)
CLIENTS = [
    {'name': 'Client A',  'url': 'client-a.com',  'sheet_id': 'YOUR_SHEET_ID_HERE'},
    {'name': 'Client B',  'url': 'client-b.com',  'sheet_id': 'YOUR_SHEET_ID_HERE'},
    {'name': 'Client C',  'url': 'client-c.com',  'sheet_id': 'YOUR_SHEET_ID_HERE'},
    # Add more clients following the same pattern
]

HINT_MAPPING = {
    'Broken internal URLs': {'severity': 'critical', 'category': 'Crawlability'},
    'Has broken bookmarks': {'severity': 'high', 'category': 'Crawlability'},
    'Query string contains a question mark': {'severity': 'low', 'category': 'URL Structure'},
    'Query string contains more than three parameters': {'severity': 'medium', 'category': 'URL Structure'},
    'URL contains whitespace': {'severity': 'high', 'category': 'URL Structure'},
    'Has link with a URL referencing LocalHost or 127.0.0.1': {'severity': 'critical', 'category': 'Crawlability'},
    'Has a link with an empty href attribute': {'severity': 'high', 'category': 'Crawlability'},
    'Has only one followed internal linking URL': {'severity': 'high', 'category': 'Crawlability'},
    'URL is orphaned and was not found by the crawler': {'severity': 'high', 'category': 'Crawlability'},
    'Canonical is malformed or empty': {'severity': 'critical', 'category': 'Indexability'},
    'Canonical loop': {'severity': 'critical', 'category': 'Indexability'},
    'Canonical points to a noindex URL': {'severity': 'critical', 'category': 'Indexability'},
    'Multiple, mismatched canonical tags': {'severity': 'critical', 'category': 'Indexability'},
    'Mismatched noindex directives in HTML and header': {'severity': 'critical', 'category': 'Indexability'},
    'Internal URL redirect broken (4XX or 5XX)': {'severity': 'critical', 'category': 'Crawlability'},
    'Internal URL is part of a chained redirect loop': {'severity': 'critical', 'category': 'Crawlability'},
    'HTML is missing or empty': {'severity': 'critical', 'category': 'On-Page SEO'},
    'Title tag is missing': {'severity': 'critical', 'category': 'On-Page SEO'},
    'Title tag is empty': {'severity': 'critical', 'category': 'On-Page SEO'},
    'Missing viewport <meta> tag in the <head>': {'severity': 'critical', 'category': 'Mobile SEO'},
    'HTTP URL contains a password input field': {'severity': 'critical', 'category': 'Security'},
    'Contains Lorem Ipsum dummy text': {'severity': 'high', 'category': 'Content Quality'},
    '<h1> tag is missing': {'severity': 'high', 'category': 'On-Page SEO'},
    'URLs with duplicate page titles': {'severity': 'high', 'category': 'On-Page SEO'},
    'Multiple <h1> tags': {'severity': 'low', 'category': 'On-Page SEO'},
    'Meta description is missing': {'severity': 'medium', 'category': 'On-Page SEO'},
    'Images with missing alt text': {'severity': 'medium', 'category': 'On-Page SEO'},
    'Internal redirected URLs': {'severity': 'medium', 'category': 'Crawlability'},
    'Reduce server response times (TTFB)': {'severity': 'high', 'category': 'Performance'},
    'Eliminate render blocking resources': {'severity': 'medium', 'category': 'Performance'},
}

SEVERITY_SCORES = {
    'critical': 100,
    'high': 75,
    'medium': 50,
    'low': 25,
}

OUTPUT_DIR = 'output'
SNAPSHOT_FILENAME = '{client_name}_latest.json'
PREVIOUS_SNAPSHOT_FILENAME = '{client_name}_previous.json'


# ─────────────────────────────────────────────────────────────────
# CLIENT LOOKUP
# ─────────────────────────────────────────────────────────────────

def get_client(name: str) -> dict | None:
    name_lower = name.lower().replace('_', ' ')
    for c in CLIENTS:
        if c['name'].lower() == name_lower:
            return c
        slug = c['name'].lower().replace(' ', '_').replace('&', 'and').replace('/', '_')
        if slug == name.lower():
            return c
    return None

SEVERITY_ORDER = ["critical", "high", "medium", "low"]
