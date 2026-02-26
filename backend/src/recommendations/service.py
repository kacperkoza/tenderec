import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from src.companies.schemas import CompanyProfile
from src.config import settings
from src.database import get_database
from src.llm.service import get_openai_client
from src.organization_classification.constants import (
    COLLECTION_NAME as ORG_CLASSIFICATION_COLLECTION,
)
from src.recommendations.schemas import MatchLevel, TenderRecommendation
from src.tenders.schemas import Tender
from src.tenders.service import load_tenders

logger = logging.getLogger(__name__)

COMPANY_PROFILES_COLLECTION = "company_profiles"
RECOMMENDATIONS_COLLECTION = "recommendations"
LLM_CONCURRENCY = 5

SYSTEM_PROMPT = """\
You are a Polish public procurement expert specializing in matching tenders to company profiles.

You receive:
1. A company profile — its industries, service categories, and target contracting authorities.
2. A single tender with its contracting organization and the organization's industries.

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

## Response format

Respond ONLY with valid JSON:
{
  "name_match": "PERFECT_MATCH" | "PARTIAL_MATCH" | "DONT_KNOW" | "NO_MATCH",
  "name_reason": "<one sentence reasoning in Polish>",
  "industry_match": "PERFECT_MATCH" | "PARTIAL_MATCH" | "DONT_KNOW" | "NO_MATCH",
  "industry_reason": "<one sentence reasoning in Polish>"
}\
"""


async def _get_org_industries() -> dict[str, list[str]]:
    db = get_database()
    collection = db[ORG_CLASSIFICATION_COLLECTION]
    cursor = collection.find({})
    docs = await cursor.to_list(length=None)

    return {doc["_id"]: [ind["industry"] for ind in doc["industries"]] for doc in docs}


def build_user_prompt(
    profile: CompanyProfile,
    tender: Tender,
    org_industries: dict[str, list[str]],
) -> str:
    company_info = profile.company_info
    criteria = profile.matching_criteria

    industries = ", ".join(company_info.industries)
    categories = "\n".join(f"- {cat}" for cat in criteria.service_categories)
    authorities = ", ".join(criteria.target_authorities)

    org = tender.metadata.organization
    org_ind = org_industries.get(org, [])
    org_ind_str = f"\n**Industries:** {', '.join(org_ind)}" if org_ind else ""

    return f"""\
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


def _call_llm(
    user_prompt: str, tender_name: str, organization: str
) -> TenderRecommendation:
    client = get_openai_client()

    response = client.chat.completions.create(
        model=settings.llm_model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = json.loads(response.choices[0].message.content)  # type: ignore[arg-type]
    return TenderRecommendation(
        tender_name=tender_name, organization=organization, **raw
    )


def _should_skip(recommendation: TenderRecommendation) -> bool:
    return (
        recommendation.name_match == MatchLevel.NO_MATCH
        and recommendation.industry_match in (MatchLevel.NO_MATCH, MatchLevel.DONT_KNOW)
    )


async def _save_recommendation(
    company_name: str,
    recommendation: TenderRecommendation,
) -> None:
    db = get_database()
    collection = db[RECOMMENDATIONS_COLLECTION]

    now = datetime.now(timezone.utc)
    document = {
        "company": company_name,
        "tender_name": recommendation.tender_name,
        "organization": recommendation.organization,
        "name_match": recommendation.name_match,
        "name_reason": recommendation.name_reason,
        "industry_match": recommendation.industry_match,
        "industry_reason": recommendation.industry_reason,
        "created_at": now,
    }

    await collection.insert_one(document)
    logger.info(
        "Saved recommendation for tender '%s' (company '%s'): name=%s, industry=%s",
        recommendation.tender_name,
        company_name,
        recommendation.name_match,
        recommendation.industry_match,
    )


async def get_company_profile(company_name: str) -> CompanyProfile:
    db = get_database()
    collection = db[COMPANY_PROFILES_COLLECTION]

    document = await collection.find_one({"_id": company_name})
    if document is None:
        raise ValueError(f"Company not found: {company_name}")

    return CompanyProfile(**document["profile"])


async def _load_from_mongo(
    company_name: str,
    name_match: MatchLevel,
    industry_match: MatchLevel,
) -> list[TenderRecommendation]:
    db = get_database()
    collection = db[RECOMMENDATIONS_COLLECTION]

    cursor = collection.find(
        {
            "company": company_name,
            "name_match": name_match,
            "industry_match": industry_match,
        }
    )
    docs = await cursor.to_list(length=None)

    org_lookup: dict[str, str] = {}
    needs_lookup = any("organization" not in doc for doc in docs)
    if needs_lookup:
        org_lookup = {t.metadata.name: t.metadata.organization for t in load_tenders()}

    return [
        TenderRecommendation(
            tender_name=doc["tender_name"],
            organization=doc.get("organization")
            or org_lookup.get(doc["tender_name"], ""),
            name_match=doc["name_match"],
            name_reason=doc["name_reason"],
            industry_match=doc["industry_match"],
            industry_reason=doc["industry_reason"],
        )
        for doc in docs
    ]


async def _classify_via_llm(company_name: str) -> None:
    profile = await get_company_profile(company_name)

    tenders = load_tenders()
    org_industries = await _get_org_industries()

    total = len(tenders)
    logger.info(
        "Processing %d tenders (%d concurrent) for '%s'",
        total,
        LLM_CONCURRENCY,
        company_name,
    )

    semaphore = asyncio.Semaphore(LLM_CONCURRENCY)
    executor = ThreadPoolExecutor(max_workers=LLM_CONCURRENCY)
    loop = asyncio.get_event_loop()

    async def _process_tender(index: int, tender: Tender) -> None:
        async with semaphore:
            logger.info(
                "[%d/%d] Evaluating tender: '%s'", index, total, tender.metadata.name
            )
            user_prompt = build_user_prompt(profile, tender, org_industries)
            recommendation = await loop.run_in_executor(
                executor,
                _call_llm,
                user_prompt,
                tender.metadata.name,
                tender.metadata.organization,
            )

            if _should_skip(recommendation):
                logger.info(
                    "Skipping tender '%s' — name=%s, industry=%s",
                    tender.metadata.name,
                    recommendation.name_match,
                    recommendation.industry_match,
                )
                return

            await _save_recommendation(company_name, recommendation)

    tasks = [_process_tender(i, tender) for i, tender in enumerate(tenders, 1)]
    await asyncio.gather(*tasks)

    executor.shutdown(wait=False)
    logger.info("Finished processing all %d tenders for '%s'", total, company_name)


async def get_recommendations(
    company_name: str,
    name_match: MatchLevel,
    industry_match: MatchLevel,
) -> list[TenderRecommendation]:
    source = settings.recommendations_source

    if source == "llm":
        await _classify_via_llm(company_name)

    return await _load_from_mongo(company_name, name_match, industry_match)
