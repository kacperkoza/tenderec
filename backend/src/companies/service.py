from pathlib import Path

COMPANY_DIR = Path(__file__).resolve().parent.parent.parent / "resources" / "company"


def get_company(company_id: str) -> dict:
    path = COMPANY_DIR / f"{company_id}.md"
    if not path.exists():
        raise ValueError(f"Company not found: {company_id}")
    return {
        "id": company_id,
        "description": path.read_text(encoding="utf-8"),
    }

