from datetime import date

from src.config import settings
from src.constants import TENDERS_PATH as TENDERS_PATH

COLLECTION_NAME = "organization_classifications"


def get_deadline_reference_date() -> date:
    if settings.tender_deadline_date is not None:
        return settings.tender_deadline_date
    return date.today()
