import logging
from datetime import datetime, timezone

from src.companies.constants import COLLECTION_NAME, EXTRACTION_SYSTEM_PROMPT
from src.companies.exceptions import LLMExtractionError
from src.companies.schemas import (
    CompanyProfile,
    CompanyProfileDocument,
    CompanyProfileResponse,
)
from src.config import settings
from src.database import get_database
from src.llm.service import get_openai_client

logger = logging.getLogger(__name__)


async def get_company(company_name: str) -> CompanyProfileResponse | None:
    db = get_database()
    collection = db[COLLECTION_NAME]

    raw = await collection.find_one({"_id": company_name})
    if raw is None:
        return None

    document = CompanyProfileDocument.from_mongo(raw)
    return document.to_response()


def extract_company_profile(company_name: str, description: str) -> CompanyProfile:
    client = get_openai_client()

    user_prompt = (
        f"## Company name\n\n{company_name}\n\n## Company description\n\n{description}"
    )

    logger.info("LLM request start for company '%s'", company_name)
    response = client.chat.completions.create(
        model=settings.llm_model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw_content = response.choices[0].message.content
    if raw_content is None:
        raise LLMExtractionError(
            f"LLM returned empty response for company '{company_name}'"
        )

    logger.info("LLM response for company '%s': %s", company_name, raw_content)
    return CompanyProfile.model_validate_json(raw_content)


async def save_company_profile(
    company_name: str, profile: CompanyProfile
) -> CompanyProfileResponse:
    db = get_database()
    collection = db[COLLECTION_NAME]

    document = CompanyProfileDocument.from_domain(
        company_name=company_name,
        profile=profile,
        created_at=datetime.now(timezone.utc),
    )

    await collection.replace_one(
        {"_id": company_name}, document.to_mongo(), upsert=True
    )

    return document.to_response()
