import json
import logging
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.companies.company_constants import COLLECTION_NAME, EXTRACTION_SYSTEM_PROMPT
from src.companies.company_exceptions import ProfileExtractionError
from src.companies.company_schemas import (
    CompanyProfile,
    CompanyProfileDocument,
    CompanyProfileResponse,
)

logger = logging.getLogger(__name__)


class CompanyService:
    def __init__(self, db: AsyncIOMotorDatabase, llm_client: ChatOpenAI) -> None:
        self.db = db
        self.llm_client = llm_client

    async def get_company(self, company_name: str) -> CompanyProfileResponse | None:
        logger.info("Looking up company profile: '%s'", company_name)
        collection = self.db[COLLECTION_NAME]

        raw = await collection.find_one({"_id": company_name})
        if raw is None:
            logger.warning("Company profile not found: '%s'", company_name)
            return None

        document = CompanyProfileDocument.from_mongo(raw)
        logger.info("Found company profile: '%s'", company_name)
        return document.to_response()

    async def extract_company_profile(
        self, company_name: str, description: str
    ) -> CompanyProfile:
        user_prompt = f"## Company name\n\n{company_name}\n\n## Company description\n\n{description}"

        logger.info(f"LLM request start for company '{company_name}'")
        response = await self.llm_client.ainvoke(
            [
                SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ],
            response_format={"type": "json_object"},
        )

        raw_content = response.content
        if not raw_content:
            raise ProfileExtractionError(
                f"LLM returned empty response for company '{company_name}'"
            )

        logger.info(f"LLM response for company '{company_name}': {raw_content}")

        data = json.loads(raw_content)
        return CompanyProfile.from_dict(data)

    async def save_company_profile(
        self, company_name: str, profile: CompanyProfile
    ) -> CompanyProfileResponse:
        logger.info("Saving company profile: '%s'", company_name)
        collection = self.db[COLLECTION_NAME]

        document = CompanyProfileDocument.from_domain(
            company_name=company_name,
            profile=profile,
            created_at=datetime.now(timezone.utc),
        )

        await collection.replace_one(
            {"_id": company_name}, document.to_mongo(), upsert=True
        )

        logger.info("Company profile saved successfully: '%s'", company_name)
        return document.to_response()
