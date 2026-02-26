import asyncio
import json
import logging
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.companies.company_schemas import (
    CompanyGeography,
    CompanyInfo,
    CompanyProfile,
    MatchingCriteria,
)
from src.config import settings
from src.feedback.feedback_constants import COLLECTION_NAME as FEEDBACK_COLLECTION
from src.organization_classification.classification_constants import (
    COLLECTION_NAME as ORG_CLASSIFICATION_COLLECTION,
)
from src.recommendations.recommendation_schemas import MatchLevel, TenderRecommendation
from src.tenders.tender_schemas import Tender
from src.tenders.tender_service import tender_service

logger = logging.getLogger(__name__)

COMPANY_PROFILES_COLLECTION = "company_profiles"
RECOMMENDATIONS_COLLECTION = "recommendations"
LLM_CONCURRENCY = 5

SYSTEM_PROMPT = """\
You are a Polish public procurement expert specializing in matching tenders to company profiles.

You receive:
1. A company profile — its industries, service categories, and target contracting authorities.
2. A single tender with its contracting organization and the organization's industries.
3. Optionally, user feedback on previously rejected tenders — use it to understand the user's \
preferences and adjust your scoring accordingly.

Your task is to evaluate the tender against the company profile on TWO separate axes.

## Match levels

For each axis assign one of:

- **PERFECT_MATCH** — direct, obvious match.
- **PARTIAL_MATCH** — plausible but indirect match.
- **DONT_KNOW** — not enough information to judge.
- **NO_MATCH** — completely unrelated.

### Axis 1 — Tender name vs. company activities (name_match)
How closely the subject of the tender aligns with the company's service categories and competencies.
- PERFECT_MATCH example: company plants trees → tender is about planting trees.
- PARTIAL_MATCH example: company plants trees → tender is about street revitalization (likely includes greenery).
- NO_MATCH example: company plants trees → tender is about IT services.

### Axis 2 — Organization industry vs. company industries (industry_match)
How closely the contracting organization's industries align with the company's industries \
and target contracting authorities.
- PERFECT_MATCH example: company targets municipal authorities → organization is a city municipality.
- PARTIAL_MATCH example: company targets municipal authorities → organization is a regional government.
- NO_MATCH example: company targets municipal authorities → organization is a private tech corporation.

## User feedback

If user feedback on rejected tenders is provided, treat it as additional signal about the user's \
preferences. For example, if the user says "too short deadline" for a tender, penalize similar \
tenders. If they say "not our area", it reinforces NO_MATCH on the name axis.

## Response format

Respond ONLY with valid JSON:
{
  "name_match": "PERFECT_MATCH" | "PARTIAL_MATCH" | "DONT_KNOW" | "NO_MATCH",
  "name_reason": "<one sentence reasoning in Polish>",
  "industry_match": "PERFECT_MATCH" | "PARTIAL_MATCH" | "DONT_KNOW" | "NO_MATCH",
  "industry_reason": "<one sentence reasoning in Polish>"
}\
"""


class RecommendationService:
    def __init__(self, db: AsyncIOMotorDatabase, llm_client: ChatOpenAI) -> None:
        self.db = db
        self.llm_client = llm_client

    async def _get_org_industries(self) -> dict[str, list[str]]:
        collection = self.db[ORG_CLASSIFICATION_COLLECTION]
        cursor = collection.find({})
        docs = await cursor.to_list(length=None)

        return {
            doc["_id"]: [ind["industry"] for ind in doc["industries"]] for doc in docs
        }

    async def _get_feedbacks(self, company_name: str) -> list[str]:
        collection = self.db[FEEDBACK_COLLECTION]
        cursor = collection.find({"company_name": company_name})
        docs = await cursor.to_list(length=None)
        return [doc["feedback_comment"] for doc in docs]

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
    ) -> TenderRecommendation:
        response = await self.llm_client.ainvoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ],
            response_format={"type": "json_object"},
        )

        raw = json.loads(response.content)  # type: ignore[arg-type]
        return TenderRecommendation(
            tender_name=tender_name, organization=organization, **raw
        )

    @staticmethod
    def _should_skip(recommendation: TenderRecommendation) -> bool:
        return (
            recommendation.name_match == MatchLevel.NO_MATCH
            and recommendation.industry_match
            in (MatchLevel.NO_MATCH, MatchLevel.DONT_KNOW)
        )

    async def _save_recommendation(
        self,
        company_name: str,
        recommendation: TenderRecommendation,
    ) -> None:
        collection = self.db[RECOMMENDATIONS_COLLECTION]

        now = datetime.now(timezone.utc)
        doc_id = {
            "company_name": company_name,
            "tender_name": recommendation.tender_name,
        }
        document = {
            "organization": recommendation.organization,
            "name_match": recommendation.name_match,
            "name_reason": recommendation.name_reason,
            "industry_match": recommendation.industry_match,
            "industry_reason": recommendation.industry_reason,
            "created_at": now,
        }

        await collection.replace_one({"_id": doc_id}, document, upsert=True)
        logger.info(
            "Saved recommendation for tender '%s' (company '%s'): name=%s, industry=%s",
            recommendation.tender_name,
            company_name,
            recommendation.name_match,
            recommendation.industry_match,
        )

    async def _get_company_profile(self, company_name: str) -> CompanyProfile:
        collection = self.db[COMPANY_PROFILES_COLLECTION]

        document = await collection.find_one({"_id": company_name})
        if document is None:
            raise ValueError(f"Company not found: {company_name}")

        raw_profile: dict = document["profile"]  # type: ignore[assignment]
        return CompanyProfile(
            company_info=CompanyInfo(**raw_profile["company_info"]),
            matching_criteria=MatchingCriteria(
                geography=CompanyGeography(
                    **raw_profile["matching_criteria"]["geography"]
                ),
                service_categories=raw_profile["matching_criteria"][
                    "service_categories"
                ],
                cpv_codes=raw_profile["matching_criteria"]["cpv_codes"],
                target_authorities=raw_profile["matching_criteria"][
                    "target_authorities"
                ],
            ),
        )

    async def _load_from_mongo(
        self,
        company_name: str,
        name_match: MatchLevel,
        industry_match: MatchLevel,
    ) -> list[TenderRecommendation]:
        collection = self.db[RECOMMENDATIONS_COLLECTION]

        cursor = collection.find(
            {
                "_id.company_name": company_name,
                "name_match": name_match,
                "industry_match": industry_match,
            }
        )
        docs = await cursor.to_list(length=None)

        org_lookup: dict[str, str] = {}
        needs_lookup = any("organization" not in doc for doc in docs)
        if needs_lookup:
            org_lookup = {
                t.metadata.name: t.metadata.organization
                for t in tender_service.load_tenders()
            }

        return [
            TenderRecommendation(
                tender_name=doc["_id"]["tender_name"],
                organization=doc.get("organization")
                or org_lookup.get(doc["_id"]["tender_name"], ""),
                name_match=doc["name_match"],
                name_reason=doc["name_reason"],
                industry_match=doc["industry_match"],
                industry_reason=doc["industry_reason"],
            )
            for doc in docs
        ]

    async def _classify_via_llm(self, company_name: str) -> None:
        profile = await self._get_company_profile(company_name)

        tenders = tender_service.load_tenders()
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
                recommendation = await self._call_llm(
                    user_prompt,
                    tender.metadata.name,
                    tender.metadata.organization,
                )

                if self._should_skip(recommendation):
                    logger.info(
                        "Skipping tender '%s' — name=%s, industry=%s",
                        tender.metadata.name,
                        recommendation.name_match,
                        recommendation.industry_match,
                    )
                    return

                await self._save_recommendation(company_name, recommendation)

        tasks = [_process_tender(i, tender) for i, tender in enumerate(tenders, 1)]
        await asyncio.gather(*tasks)

        logger.info(f"Finished processing all {total} tenders for '{company_name}'")

    async def get_recommendations(
        self,
        company_name: str,
        name_match: MatchLevel,
        industry_match: MatchLevel,
    ) -> list[TenderRecommendation]:
        source = settings.recommendations_source

        if source == "llm":
            await self._classify_via_llm(company_name)

        return await self._load_from_mongo(company_name, name_match, industry_match)

    async def refresh_recommendation(
        self,
        company_name: str,
        tender_name: str,
    ) -> TenderRecommendation:
        tender = tender_service.get_tender_by_name(tender_name)
        if tender is None:
            raise ValueError(f"Tender not found: {tender_name}")

        profile = await self._get_company_profile(company_name)
        org_industries = await self._get_org_industries()
        feedbacks = await self._get_feedbacks(company_name)

        user_prompt = self.build_user_prompt(profile, tender, org_industries, feedbacks)

        recommendation = await self._call_llm(
            user_prompt,
            tender.metadata.name,
            tender.metadata.organization,
        )

        await self._save_recommendation(company_name, recommendation)
        return recommendation
