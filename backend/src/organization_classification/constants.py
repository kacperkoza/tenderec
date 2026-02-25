from datetime import date
from pathlib import Path

RESOURCES_DIR = Path(__file__).resolve().parent.parent.parent / "resources"

TENDERS_PATH = RESOURCES_DIR / "tender" / "tenders_sublist.json"
INDUSTRIES_OUTPUT_PATH = RESOURCES_DIR / "organization_by_industry" / "organizations_by_industry.json"

# Test data are from the past, so we set a fixed "today" date to ensure the filtering logic works as expected.
TODAY = date(2026, 1, 10)

