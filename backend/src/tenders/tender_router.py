from fastapi import APIRouter, Depends, HTTPException, status

from src.tenders.tender_dependencies import get_tender_service
from src.tenders.tender_schemas import (
    TenderQuestionRequest,
    TenderQuestionResponse,
    TenderResponse,
)
from src.tenders.tender_service import TenderService

router = APIRouter(prefix="/tenders", tags=["tenders"])


@router.get(
    "/{tender_name}",
    response_model=TenderResponse,
    description="Get tender details by name.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Tender not found"},
    },
)
async def get_tender(
    tender_name: str,
    service: TenderService = Depends(get_tender_service),
) -> TenderResponse:
    tender = service.get_tender_by_name(tender_name)
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


@router.post(
    "/ask",
    response_model=TenderQuestionResponse,
    description="Ask a question about a specific tender. "
    "A LangChain agent analyzes tender details (name, organization, dates, files) "
    "and generates an answer.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Tender not found"},
    },
)
async def ask_tender_question(
    body: TenderQuestionRequest,
    service: TenderService = Depends(get_tender_service),
) -> TenderQuestionResponse:
    try:
        answer = await service.ask_question(
            body.tender_name, body.question, body.company_name
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return TenderQuestionResponse(
        tender_name=body.tender_name,
        question=body.question,
        answer=answer,
    )
