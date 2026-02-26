from fastapi import APIRouter, HTTPException, status

from src.tenders.tender_schemas import TenderResponse
from src.tenders.tender_service import tender_service

router = APIRouter(prefix="/tenders", tags=["tenders"])


@router.get(
    "/{tender_name}",
    response_model=TenderResponse,
    description="Get tender details by name.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Tender not found"},
    },
)
async def get_tender(tender_name: str) -> TenderResponse:
    tender = tender_service.get_tender_by_name(tender_name)
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tender '{tender_name}' not found",
        )

    return TenderResponse(
        tender_url=tender.tender_url,
        name=tender.metadata.name,
        organization=tender.metadata.organization,
        submission_deadline=tender.metadata.submission_deadline,
        initiation_date=tender.metadata.initiation_date,
        procedure_type=tender.metadata.procedure_type,
        source_type=tender.metadata.source_type,
        files_count=tender.files_count,
        file_urls=tender.file_urls,
    )
