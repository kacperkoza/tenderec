import json
from functools import lru_cache

from src.constants import TENDERS_PATH
from src.tenders.tender_schemas import Tender, TenderMetadata


class TenderService:
    @staticmethod
    @lru_cache(maxsize=1)
    def load_tenders() -> list[Tender]:
        with open(TENDERS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [
            Tender(
                tender_url=t["tender_url"],
                metadata=TenderMetadata(**t["metadata"]),
                files_count=t["files_count"],
                file_urls=t["file_urls"],
            )
            for t in data["tenders"]
        ]

    def get_tender_by_name(self, name: str) -> Tender | None:
        tenders = self.load_tenders()
        for tender in tenders:
            if tender.metadata.name == name:
                return tender
        return None


tender_service = TenderService()
