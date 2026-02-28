import asyncio
import json
import logging
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.companies.company_constants import (
    COLLECTION_NAME as COMPANY_PROFILES_COLLECTION,
)
from src.companies.company_schemas import CompanyProfile, CompanyProfileDocument
from src.config import settings
from src.feedback.feedback_constants import COLLECTION_NAME as FEEDBACK_COLLECTION
from src.organization_classification.classification_constants import (
    COLLECTION_NAME as ORG_CLASSIFICATION_COLLECTION,
)
from src.organization_classification.classification_schemas import (
    OrganizationClassificationDocument,
)
from src.recommendations.recommendation_constants import (
    COLLECTION_NAME as RECOMMENDATIONS_COLLECTION,
    LLM_CONCURRENCY,
    RECOMMENDATION_SYSTEM_PROMPT,
)
from src.recommendations.recommendation_schemas import (
    MatchLevel,
    RecommendationDocument,
    RecommendationResult,
    TenderRecommendation,
)
from src.tenders.tender_schemas import Tender
from src.tenders.tender_service import TenderService

logger = logging.getLogger(__name__)


class RecommendationService:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        llm_client: ChatOpenAI,
        tender_service: TenderService,
    ) -> None:
        self.db = db
        self.llm_client = llm_client
        self.tender_service = tender_service

    async def _get_org_industries(self) -> dict[str, list[str]]:
        logger.info("Loading organization industries from MongoDB")
        collection = self.db[ORG_CLASSIFICATION_COLLECTION]
        cursor = collection.find({})
        docs = await cursor.to_list(length=None)
        result = {
            doc_obj.id: [ind.industry for ind in doc_obj.industries]
            for doc_obj in (
                OrganizationClassificationDocument.from_mongo(doc) for doc in docs
            )
        }
        logger.info("Loaded industries for %d organizations", len(result))
        return result

    async def _get_feedbacks(self, company_name: str) -> list[str]:
        logger.info("Loading feedbacks for company '%s'", company_name)
        collection = self.db[FEEDBACK_COLLECTION]
        cursor = collection.find({"company_name": company_name})
        docs = await cursor.to_list(length=None)
        feedbacks = [doc["feedback_comment"] for doc in docs]
        logger.info(
            "Loaded %d feedbacks for company '%s'", len(feedbacks), company_name
        )
        return feedbacks

    @staticmethod
    def build_user_prompt(
        profile: CompanyProfile,
        tender: Tender,
        org_industries: dict[str, list[str]],
        feedbacks: list[str],
    ) -> str:
        company_info = profile.company_info
        criteria = profile.matching_criteria

        industries = ", ".join(company_info.industries)
        categories = "\n".join(f"- {cat}" for cat in criteria.service_categories)
        authorities = ", ".join(criteria.target_authorities)

        org = tender.metadata.organization
        org_ind = org_industries.get(org, [])
        org_ind_str = f"\n**Industries:** {', '.join(org_ind)}" if org_ind else ""

        prompt = f"""\
## Company profile: {company_info.name}

### Company's Industries
{industries}

### Company's Service categories
{categories}

### Company's Target contracting authorities
{authorities}

## Tender
**Name:** {tender.metadata.name}
**Organization:** {org}{org_ind_str}\
"""

        if feedbacks:
            feedback_lines = "\n".join(f"- {fb}" for fb in feedbacks)
            prompt += f"""

## User feedback on previously rejected tenders
{feedback_lines}\
"""

        return prompt

    async def _call_llm(
        self, user_prompt: str, tender_name: str, organization: str
    ) -> RecommendationResult:
        logger.info("Calling LLM for tender='%s', org='%s'", tender_name, organization)
        response = await self.llm_client.ainvoke(
            [
                SystemMessage(content=RECOMMENDATION_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ],
            response_format={"type": "json_object"},
        )

        raw = json.loads(response.content)  # type: ignore[arg-type]
        result = RecommendationResult(
            tender_name=tender_name,
            organization=organization,
            name_match=MatchLevel(raw["name_match"]),
            name_reason=raw["name_reason"],
            industry_match=MatchLevel(raw["industry_match"]),
            industry_reason=raw["industry_reason"],
        )
        logger.info(
            "LLM result for tender='%s': name_match=%s, industry_match=%s",
            tender_name,
            result.name_match,
            result.industry_match,
        )
        return result

    @staticmethod
    def _should_skip(result: RecommendationResult) -> bool:
        return result.name_match == MatchLevel.NO_MATCH and result.industry_match in (
            MatchLevel.NO_MATCH,
            MatchLevel.DONT_KNOW,
        )

    async def _save_recommendation(
        self,
        company_name: str,
        result: RecommendationResult,
    ) -> None:
        now = datetime.now(timezone.utc)
        document = RecommendationDocument.from_domain(company_name, result, now)
        mongo_doc = document.to_mongo()

        collection = self.db[RECOMMENDATIONS_COLLECTION]
        await collection.replace_one({"_id": mongo_doc["_id"]}, mongo_doc, upsert=True)
        logger.info(
            "Saved recommendation for tender '%s' (company '%s'): name=%s, industry=%s",
            result.tender_name,
            company_name,
            result.name_match,
            result.industry_match,
        )

    async def _get_company_profile(self, company_name: str) -> CompanyProfile:
        logger.info("Loading company profile for '%s'", company_name)
        collection = self.db[COMPANY_PROFILES_COLLECTION]

        raw_doc = await collection.find_one({"_id": company_name})
        if raw_doc is None:
            logger.warning("Company not found: '%s'", company_name)
            raise ValueError(f"Company not found: {company_name}")

        return CompanyProfileDocument.from_mongo(raw_doc).profile

    async def _load_from_mongo(
        self,
        company_name: str,
        name_match: MatchLevel,
        industry_match: MatchLevel,
    ) -> list[TenderRecommendation]:
        logger.info(
            "Loading recommendations from MongoDB for company='%s', name_match=%s, industry_match=%s",
            company_name,
            name_match,
            industry_match,
        )
        collection = self.db[RECOMMENDATIONS_COLLECTION]

        cursor = collection.find(
            {
                "_id.company_name": company_name,
                "name_match": name_match,
                "industry_match": industry_match,
            }
        )
        raw_docs = await cursor.to_list(length=None)

        documents = [RecommendationDocument.from_mongo(doc) for doc in raw_docs]

        # Back-fill organization for legacy docs that may lack it
        org_lookup: dict[str, str] = {}
        needs_lookup = any(not doc.organization for doc in documents)
        if needs_lookup:
            org_lookup = {
                t.metadata.name: t.metadata.organization
                for t in self.tender_service.load_tenders()
            }
            for doc in documents:
                if not doc.organization:
                    doc.organization = org_lookup.get(doc.tender_name, "")

        return [doc.to_response() for doc in documents]

    async def _classify_via_llm(self, company_name: str) -> None:
        logger.info("Starting LLM classification for company '%s'", company_name)
        profile = await self._get_company_profile(company_name)

        tenders = self.tender_service.load_tenders()
        org_industries = await self._get_org_industries()
        feedbacks = await self._get_feedbacks(company_name)

        total = len(tenders)
        logger.info(
            "Processing %d tenders (%d concurrent) for '%s'",
            total,
            LLM_CONCURRENCY,
            company_name,
        )

        semaphore = asyncio.Semaphore(LLM_CONCURRENCY)

        async def _process_tender(index: int, tender: Tender) -> None:
            async with semaphore:
                logger.info(
                    "[%d/%d] Evaluating tender: '%s'",
                    index,
                    total,
                    tender.metadata.name,
                )
                user_prompt = self.build_user_prompt(
                    profile, tender, org_industries, feedbacks
                )
                result = await self._call_llm(
                    user_prompt,
                    tender.metadata.name,
                    tender.metadata.organization,
                )

                if self._should_skip(result):
                    logger.info(
                        "Skipping tender '%s' — name=%s, industry=%s",
                        tender.metadata.name,
                        result.name_match,
                        result.industry_match,
                    )
                    return

                await self._save_recommendation(company_name, result)

        tasks = [_process_tender(i, tender) for i, tender in enumerate(tenders, 1)]
        await asyncio.gather(*tasks)

        logger.info("Finished processing all %d tenders for '%s'", total, company_name)

    async def get_recommendations(
        self,
        company_name: str,
        name_match: MatchLevel,
        industry_match: MatchLevel,
    ) -> list[TenderRecommendation]:
        source = settings.recommendations_source
        logger.info(
            "Getting recommendations for company='%s' (source=%s, name_match=%s, industry_match=%s)",
            company_name,
            source,
            name_match,
            industry_match,
        )

        if source == "llm":
            await self._classify_via_llm(company_name)

        results = await self._load_from_mongo(company_name, name_match, industry_match)
        logger.info(
            "Returning %d recommendations for company='%s'",
            len(results),
            company_name,
        )
        return results

    async def refresh_recommendation(
        self,
        company_name: str,
        tender_name: str,
    ) -> TenderRecommendation:
        logger.info(
            "Refreshing recommendation for company='%s', tender='%s'",
            company_name,
            tender_name,
        )
        tender = self.tender_service.get_tender_by_name(tender_name)
        if tender is None:
            logger.warning("Tender not found for refresh: '%s'", tender_name)
            raise ValueError(f"Tender not found: {tender_name}")

        profile = await self._get_company_profile(company_name)
        org_industries = await self._get_org_industries()
        feedbacks = await self._get_feedbacks(company_name)

        user_prompt = self.build_user_prompt(profile, tender, org_industries, feedbacks)

        result = await self._call_llm(
            user_prompt,
            tender.metadata.name,
            tender.metadata.organization,
        )

        await self._save_recommendation(company_name, result)
        logger.info(
            "Refresh complete for tender='%s': name_match=%s, industry_match=%s",
            tender_name,
            result.name_match,
            result.industry_match,
        )
        return RecommendationDocument.from_domain(
            company_name, result, datetime.now(timezone.utc)
        ).to_response()
