from pathlib import Path

RESOURCES_DIR = Path(__file__).resolve().parent.parent.parent / "resources"

TENDERS_PATH = RESOURCES_DIR / "tender" / "tenders_sublist.json"
INDUSTRIES_PATH = RESOURCES_DIR / "organization_by_industry" / "organizations_by_industry.json"
COMPANY_DIR = RESOURCES_DIR / "company"

SCORE_THRESHOLD = 0.7

COMPANY_REGISTRY: dict[str, str] = {
    "greenworks_company": "GreenWorks Infrastructure Ltd.",
}

