from src.companies.schemas import CompanyProfile
from src.database import get_database

COMPANY_PROFILES_COLLECTION = "company_profiles"


SYSTEM_PROMPT = """\
Jesteś ekspertem ds. zamówień publicznych w Polsce. Twoim zadaniem jest ocena, \
które przetargi najlepiej pasują do profilu firmy.

Na podstawie profilu firmy przeanalizuj poniższą listę przetargów \
i dla każdego z nich oceń dopasowanie w skali 0-100. \
Zwróć wyniki posortowane od najlepiej dopasowanego.

Dla każdego przetargu podaj:
- wynik dopasowania (0-100)
- krótkie uzasadnienie dopasowania po polsku

Odpowiedz WYŁĄCZNIE poprawnym JSON-em w formacie:
{
  "recommendations": [
    {
      "tender_name": "<nazwa przetargu>",
      "score": <0-100>,
      "reason": "<uzasadnienie>"
    }
  ]
}\
"""


def build_user_prompt(profile: CompanyProfile) -> str:
    company_info = profile.company_info
    criteria = profile.matching_criteria

    industries = ", ".join(company_info.industries)
    categories = "\n".join(f"- {cat}" for cat in criteria.service_categories)
    authorities = ", ".join(criteria.target_authorities)
    prompt = f"""\
## Profil firmy: {company_info.name}

### Branże
{industries}

### Kategorie usług
{categories}

### Docelowi zamawiający
{authorities}\
"""
    print(prompt)
    return prompt
    return prompt


async def get_company_profile(company_name: str) -> CompanyProfile:
    db = get_database()
    collection = db[COMPANY_PROFILES_COLLECTION]

    document = await collection.find_one({"_id": company_name})
    if document is None:
        raise ValueError(f"Company not found: {company_name}")

    return CompanyProfile(**document["profile"])
