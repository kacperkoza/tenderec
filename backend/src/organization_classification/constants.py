from datetime import date

from src.constants import TENDERS_PATH as TENDERS_PATH

COLLECTION_NAME = "organization_classifications"

# Test data are from the past, so we set a fixed "today" date to ensure the filtering logic works as expected.
TODAY = date(2026, 1, 10)
