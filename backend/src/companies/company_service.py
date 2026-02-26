import json
import logging
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from openai import OpenAI

from src.companies.company_constants import COLLECTION_NAME, EXTRACTION_SYSTEM_PROMPT
from src.companies.company_exceptions import ProfileExtractionError
from src.companies.company_schemas import (
    CompanyGeography,
    CompanyInfo,
    CompanyProfile,
    CompanyProfileDocument,
    CompanyProfileResponse,
    MatchingCriteria,
)
from src.config import settings

logger = logging.getLogger(__name__)


class CompanyService:
    def __init__(self, db: AsyncIOMotorDatabase, client: OpenAI) -> None:
        self.db = db
        self.client = client

    async def get_company(self, company_name: str) -> CompanyProfileResponse | None:
        collection = self.db[COLLECTION_NAME]

        raw = await collection.find_one({"_id": company_name})
        if raw is None:
            return None

        document = CompanyProfileDocument.from_mongo(raw)
        return document.to_response()

    def extract_company_profile(
        self, company_name: str, description: str
    ) -> CompanyProfile:
        user_prompt = f"## Company name\n\n{company_name}\n\n## Company description\n\n{description}"

        logger.info("LLM request start for company '%s'", company_name)
        response = self.client.chat.completions.create(
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
            raise ProfileExtractionError(
                f"LLM returned empty response for company '{company_name}'"
            )

        logger.info("LLM response for company '%s': %s", company_name, raw_content)

        data = json.loads(raw_content)
        return CompanyProfile(
            company_info=CompanyInfo(**data["company_info"]),
            matching_criteria=MatchingCriteria(
                geography=CompanyGeography(**data["matching_criteria"]["geography"]),
                service_categories=data["matching_criteria"]["service_categories"],
                cpv_codes=data["matching_criteria"]["cpv_codes"],
                target_authorities=data["matching_criteria"]["target_authorities"],
            ),
        )

    async def save_company_profile(
        self, company_name: str, profile: CompanyProfile
    ) -> CompanyProfileResponse:
        collection = self.db[COLLECTION_NAME]

        document = CompanyProfileDocument.from_domain(
            company_name=company_name,
            profile=profile,
            created_at=datetime.now(timezone.utc),
        )

        await collection.replace_one(
            {"_id": company_name}, document.to_mongo(), upsert=True
        )

        return document.to_response()
