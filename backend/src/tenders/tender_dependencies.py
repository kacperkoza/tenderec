from fastapi import Request

from src.tenders.tender_service import TenderService


def get_tender_service(request: Request) -> TenderService:
    return request.app.state.tender_service  # type: ignore[no-any-return]
