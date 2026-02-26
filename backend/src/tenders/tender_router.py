import logging

from fastapi import APIRouter, Depends, HTTPException, status

from src.tenders.tender_dependencies import get_tender_service
from src.tenders.tender_schemas import (
    TenderQuestionRequest,
    TenderQuestionResponse,
    TenderResponse,
)
from src.tenders.tender_service import TenderService

logger = logging.getLogger(__name__)

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
    logger.info("GET tender: '%s'", tender_name)
    tender = service.get_tender_by_name(tender_name)
    if not tender:
        logger.warning("Tender not found: '%s'", tender_name)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tender '{tender_name}' not found",
        )

    logger.info(
        "Returning tender '%s' (org: '%s')", tender_name, tender.metadata.organization
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
    logger.info(
        "POST ask question for tender='%s', company='%s': '%s'",
        body.tender_name,
        body.company_name,
        body.question,
    )
    try:
        answer = await service.ask_question(
            body.tender_name, body.question, body.company_name
        )
    except ValueError as exc:
        logger.warning(
            "Ask question failed for tender='%s': %s",
            body.tender_name,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    logger.info(
        "Answered question for tender='%s' (answer length: %d chars)",
        body.tender_name,
        len(answer),
    )
    return TenderQuestionResponse(
        tender_name=body.tender_name,
        question=body.question,
        answer=answer,
    )
