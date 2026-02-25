import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from itertools import islice

from fastapi.concurrency import run_in_threadpool

from src.companies.schemas import CompanyProfile
from src.config import settings
from src.database import get_database
from src.llm.service import get_openai_client
from src.organization_classification.constants import (
    COLLECTION_NAME as ORG_CLASSIFICATION_COLLECTION,
)
from src.recommendations.schemas import RecommendationsResponse, TenderRecommendation
from src.tenders.schemas import Tender
from src.tenders.service import load_tenders

logger = logging.getLogger(__name__)

COMPANY_PROFILES_COLLECTION = "company_profiles"
RECOMMENDATIONS_COLLECTION = "recommendations"
ORG_LIMIT = 1


SYSTEM_PROMPT = """\
You are a Polish public procurement expert specializing in matching tenders to company profiles.

You receive:
1. A company profile — its industries, service categories, and target contracting authorities.
2. A list of tenders grouped by contracting organization. \
Each organization has its industries listed in square brackets.

Your task is to evaluate how well each tender matches the company profile.

## Scoring (0-100)

The score consists of two components:

1. **Tender name relevance to company activities (0-70 pts)**
   Evaluate how closely the subject of the tender (tender name) aligns with the company's \
service categories and competencies. Full match = 70 pts, no relation = 0 pts.

2. **Industry relevance (0-30 pts)**
   Evaluate how closely the contracting organization's industries align with the company's \
industries and target authorities. Full match = 30 pts, no relation = 0 pts.

Final score = sum of both components.

## Response format

Respond ONLY with valid JSON:
{
  "recommendations": [
    {
      "tender_name": "<tender name>",
      "score": <0-100>,
      "name_relevance_score": <0-70>,
      "name_relevance_reason": "<one sentence reasoning in Polish>",
      "industry_relevance_score": <0-30>,
      "industry_relevance_reason": "<one sentence reasoning in Polish>"
    }
  ]
}

Return results sorted descending by score. Include ALL tenders.\
"""


def _group_tenders_by_organization(
    tenders: list[Tender],
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for tender in tenders:
        org = tender.metadata.organization
        grouped[org].append(tender.metadata.name)
    return dict(grouped)


async def _get_org_industries() -> dict[str, list[str]]:
    db = get_database()
    collection = db[ORG_CLASSIFICATION_COLLECTION]
    cursor = collection.find({})
    docs = await cursor.to_list(length=None)

    return {doc["_id"]: [ind["industry"] for ind in doc["industries"]] for doc in docs}


def _build_tenders_section(
    grouped: dict[str, list[str]],
    org_industries: dict[str, list[str]],
) -> str:
    lines: list[str] = []
    for org, tender_names in grouped.items():
        industries = org_industries.get(org, [])
        industries_str = f" [{', '.join(industries)}]" if industries else ""

        lines.append(f"### Organization: {org}{industries_str}")
        lines.append("Tenders:")
        for name in tender_names:
            lines.append(f"{name}")
        lines.append("")

    return "\n".join(lines)


def build_user_prompt(
    profile: CompanyProfile,
    grouped_tenders: dict[str, list[str]],
    org_industries: dict[str, list[str]],
) -> str:
    company_info = profile.company_info
    criteria = profile.matching_criteria

    industries = ", ".join(company_info.industries)
    categories = "\n".join(f"- {cat}" for cat in criteria.service_categories)
    authorities = ", ".join(criteria.target_authorities)
    tenders_section = _build_tenders_section(grouped_tenders, org_industries)

    return f"""\
## Company profile: {company_info.name}

### Industries
{industries}

### Service categories
{categories}

### Target contracting authorities
{authorities}

## Tenders

{tenders_section}\
"""


def _call_llm(user_prompt: str) -> list[TenderRecommendation]:
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
    return [TenderRecommendation(**r) for r in raw["recommendations"]]


async def _save_recommendations(
    company_name: str,
    recommendations: list[TenderRecommendation],
) -> datetime:
    db = get_database()
    collection = db[RECOMMENDATIONS_COLLECTION]

    now = datetime.now(timezone.utc)
    document = {
        "_id": company_name,
        "recommendations": [r.model_dump() for r in recommendations],
        "created_at": now,
    }

    await collection.replace_one({"_id": company_name}, document, upsert=True)
    logger.info("Saved %d recommendations for '%s'", len(recommendations), company_name)
    return now


async def get_company_profile(company_name: str) -> CompanyProfile:
    db = get_database()
    collection = db[COMPANY_PROFILES_COLLECTION]

    document = await collection.find_one({"_id": company_name})
    if document is None:
        raise ValueError(f"Company not found: {company_name}")

    return CompanyProfile(**document["profile"])


async def get_recommendations(company_name: str) -> None:
    profile = await get_company_profile(company_name)

    tenders = load_tenders()
    all_grouped = _group_tenders_by_organization(tenders)
    org_industries = await _get_org_industries()

    limited_grouped = dict(islice(all_grouped.items(), ORG_LIMIT))
    logger.info(
        "Processing %d/%d organizations for '%s'",
        len(limited_grouped),
        len(all_grouped),
        company_name,
    )

    user_prompt = build_user_prompt(profile, limited_grouped, org_industries)
    print(user_prompt)
