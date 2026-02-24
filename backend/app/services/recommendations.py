import json
from pathlib import Path

from app.services.matching import match_company_to_industries

TENDERS_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "resources"
    / "tender"
    / "tenders_sublist.json"
)

INDUSTRIES_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "resources"
    / "organization_by_industry"
    / "organizations_by_industry.json"
)

# Map companyId -> company profile path
COMPANY_REGISTRY: dict[str, str] = {
    "greenworks_company": "GreenWorks Infrastructure Ltd.",
}

SCORE_THRESHOLD = 0.7


def _load_tenders() -> list[dict]:
    with open(TENDERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["tenders"]


def _load_industries() -> dict[str, str]:
    """Returns a flat map: organization_name -> industry."""
    with open(INDUSTRIES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    org_to_industry: dict[str, str] = {}
    for group in data["industries"]:
        for org in group["organizations"]:
            org_to_industry[org] = group["industry"]
    return org_to_industry


def get_recommendations(company_id: str, threshold: float = SCORE_THRESHOLD) -> dict:
    company_name = COMPANY_REGISTRY.get(company_id)
    if not company_name:
        raise ValueError(f"Unknown company_id: {company_id}")

    # 1. Get LLM industry scores for the company
    match_result = match_company_to_industries()

    # 2. Filter industries above threshold
    relevant_industries: dict[str, dict] = {
        m["industry"]: m
        for m in match_result["matches"]
        if m["score"] >= threshold
    }

    if not relevant_industries:
        return {
            "company_id": company_id,
            "company": company_name,
            "threshold": threshold,
            "total": 0,
            "recommendations": [],
        }

    # 3. Build org -> industry map from file
    org_to_industry = _load_industries()

    # 4. Load tenders and match
    tenders = _load_tenders()
    recommendations = []

    for tender in tenders:
        org = tender["metadata"]["organization"]
        industry = org_to_industry.get(org)
        if not industry or industry not in relevant_industries:
            continue

        match = relevant_industries[industry]
        recommendations.append({
            "tender_url": tender["tender_url"],
            "name": tender["metadata"]["name"],
            "organization": org,
            "industry": industry,
            "score": match["score"],
            "reasoning": match["reasoning"],
        })

    # Sort by score desc, then by name
    recommendations.sort(key=lambda x: (-x["score"], x["name"]))

    return {
        "company_id": company_id,
        "company": company_name,
        "threshold": threshold,
        "total": len(recommendations),
        "recommendations": recommendations,
    }

