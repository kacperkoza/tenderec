import json

from src.constants import TENDERS_PATH
from src.tenders.schemas import Tender


def load_tenders() -> list[Tender]:
    with open(TENDERS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Tender(**t) for t in data["tenders"]]
