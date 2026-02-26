import json
from functools import lru_cache

from src.constants import TENDERS_PATH
from src.tenders.schemas import Tender


@lru_cache(maxsize=1)
def load_tenders() -> list[Tender]:
    with open(TENDERS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Tender(**t) for t in data["tenders"]]


def get_tender_by_name(name: str) -> Tender | None:
    tenders = load_tenders()
    for tender in tenders:
        if tender.metadata.name == name:
            return tender
    return None
