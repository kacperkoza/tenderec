import json
import logging

from datetime import datetime, timezone

from src.companies.schemas import CompanyProfile, CompanyProfileResponse
from src.config import settings
from src.database import get_database
from src.llm.service import get_openai_client

COLLECTION_NAME = "company_profiles"

EXTRACTION_SYSTEM_PROMPT = """\
Jesteś ekspertem od analizy profili firm w kontekście polskiego rynku zamówień publicznych.

Dostajesz nazwę firmy i jej opis. Twoim zadaniem jest wyekstrahować kluczowe informacje \
o firmie w ustrukturyzowanym formacie JSON.

WAŻNE: Wszystkie wartości tekstowe (nazwy branż, kategorie usług, kody CPV, typy zamawiających, \
nazwy krajów) muszą być zapisane PO POLSKU.

Odpowiedz WYŁĄCZNIE poprawnym JSON-em w formacie:
{
  "company_info": {
    "name": "<pełna nazwa firmy>",
    "industries": ["<branża 1>", "<branża 2>"]
  },
  "matching_criteria": {
    "service_categories": [
      "<kategoria usług 1>",
      "<kategoria usług 2>"
    ],
    "cpv_codes": [
      "<kod CPV z numerem, np. 77310000-6>"
    ],
    "target_authorities": [
      "<typ zamawiającego 1>",
      "<typ zamawiającego 2>"
    ],
    "geography": {
      "primary_country": "<główny kraj działalności>"
    }
  }
}

Zasady:
- "industries": główne branże, w których firma działa (po polsku)
- "service_categories": konkretne kategorie usług/produktów firmy (po polsku, szczegółowo)
- "cpv_codes": kody CPV (Wspólny Słownik Zamówień) pasujące do usług firmy, w formacie "XXXXXXXX-X"
- "target_authorities": typy zamawiających publicznych, do których firma mogłaby składać oferty (po polsku)
- "geography.primary_country": główny kraj działalności firmy (po polsku)

Bądź precyzyjny i wyciągaj informacje bezpośrednio z opisu. Jeśli czegoś brakuje, wnioskuj \
na podstawie kontekstu branżowego.

Nie dodawaj żadnego tekstu poza JSON-em.\
"""
logger = logging.getLogger(__name__)


async def get_company(company_name: str) -> CompanyProfileResponse:
    db = get_database()
    collection = db[COLLECTION_NAME]

    document = await collection.find_one({"_id": company_name})
    if document is None:
        raise ValueError(f"Company not found: {company_name}")
    company = CompanyProfileResponse(
        company_name=document["_id"],
        profile=document["profile"],
        created_at=document["created_at"],
    )
    logger.info("Get company profile: '%s'", company_name)
    return company


def extract_company_profile(company_name: str, description: str) -> CompanyProfile:
    client = get_openai_client()

    user_prompt = f"## Nazwa firmy\n\n{company_name}\n\n## Opis firmy\n\n{description}"

    response = client.chat.completions.create(
        model=settings.llm_model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = json.loads(response.choices[0].message.content)  # type: ignore[arg-type]
    return CompanyProfile(**raw)


async def create_company_profile(
        company_name: str, profile: CompanyProfile
) -> CompanyProfileResponse:
    db = get_database()
    collection = db[COLLECTION_NAME]

    now = datetime.now(timezone.utc)
    document = {
        "_id": company_name,
        "profile": profile.model_dump(),
        "created_at": now,
    }

    await collection.replace_one({"_id": company_name}, document, upsert=True)

    return CompanyProfileResponse(
        company_name=company_name,
        profile=profile,
        created_at=now,
    )
