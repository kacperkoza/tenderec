import json
import logging
import math

from fastapi.concurrency import run_in_threadpool
from pymongo import ReplaceOne

from src.companies.service import get_company
from src.config import settings
from src.database import get_database
from src.llm.service import get_openai_client
from src.recommendations import constants as rec_constants
from src.recommendations.schemas import MatchCompanyResponse

logger = logging.getLogger(__name__)

BATCH_COUNT = 20
COLLECTION_NAME = "tender_matches"

MATCHING_SYSTEM_PROMPT = """\
Jesteś ekspertem od polskiego rynku zamówień publicznych i analizy dopasowania firm do przetargów.

Dostajesz:
1. Profil firmy (usługi, branża, kryteria dopasowania).
2. Listę przetargów — każdy z nazwą przetargu i nazwą organizacji zamawiającej.

Twoim zadaniem jest ocenić dopasowanie firmy do KAŻDEGO przetargu \
według 3 kryteriów punktowych (łącznie max 100 pkt).

Dla KAŻDEGO kryterium podaj score ORAZ krótkie uzasadnienie (reasoning) po polsku.
Na końcu dodaj ogólne reasoning podsumowujące ocenę.

## KRYTERIA OCENY

### 1. Dopasowanie Przedmiotu Zamówienia — subject_match (Max 50 pkt)
Porównaj nazwę przetargu z listą usług firmy (service_categories).
- 0 pkt: Całkowity brak związku (np. analizatory gazów, środki smarne, IT, gdy firma zajmuje się zielenią).
- 25 pkt: Częściowe powiązanie (np. duża budowa drogi, gdzie zieleń to tylko mały ułamek prac).
- 50 pkt: Idealne dopasowanie do głównych usług (np. wycinka drzew, utrzymanie zieleni).

### 2. Charakter Zamówienia: Usługa vs Dostawa — service_vs_delivery (Max 30 pkt)
Firma świadczy usługi i wykonuje prace, nie jest hurtownią. \
Oceń charakter czynności wynikający z nazwy przetargu.
- 0 pkt: Czysta dostawa towarów (np. "Dostawa środków smarnych", "Dostawa sprzętu").
- 15 pkt: Zamówienie mieszane (Dostawa wraz z montażem lub nasadzeniem).
- 30 pkt: Czysta usługa / prace fizyczne (utrzymanie, koszenie, budowa).

### 3. Profil Zamawiającego — authority_profile (Max 20 pkt)
Oceń, czy organizacja zamawiająca pasuje do preferowanych klientów firmy (target_authorities).
- 0 pkt: Podmioty całkowicie niezwiązane z profilem.
- 10 pkt: Organizacje publiczne, ale poza głównym nurtem działania firmy (np. szpitale, zakłady karne).
- 20 pkt: Idealny klient z grupy docelowej (np. Gminy, Zarządy Dróg, Zarządy Zieleni Miejskiej).

Odpowiedz WYŁĄCZNIE poprawnym JSON-em w formacie:
{
  "matches": [
    {
      "tender_name": "<nazwa przetargu>",
      "organization": "<nazwa organizacji>",
      "total_score": <int 0-100>,
      "criteria": {
        "subject_match": {"score": <int 0-50>, "reasoning": "<uzasadnienie>"},
        "service_vs_delivery": {"score": <int 0-30>, "reasoning": "<uzasadnienie>"},
        "authority_profile": {"score": <int 0-20>, "reasoning": "<uzasadnienie>"}
      },
      "reasoning": "<ogólne uzasadnienie po polsku, 1-2 zdania>"
    }
  ]
}

Posortuj wynik od najwyższego total_score do najniższego.
Nie dodawaj żadnego tekstu poza JSON-em.\
"""


async def _load_company_profile_text(company_name: str) -> str:
    company = await get_company(company_name)
    profile = company.profile

    info = profile.company_info
    criteria = profile.matching_criteria

    lines = [
        f"Nazwa firmy: {info.name}",
        f"Branże: {', '.join(info.industries)}",
        f"Kraj działania: {criteria.geography.primary_country}",
        f"Kategorie usług: {', '.join(criteria.service_categories)}",
        f"Kody CPV: {', '.join(criteria.cpv_codes)}",
        f"Preferowani zamawiający: {', '.join(criteria.target_authorities)}",
    ]
    return "\n".join(lines)


def _load_tenders() -> list[dict]:
    with open(rec_constants.TENDERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["tenders"]


def _classify_batch(company_profile_text: str, tender_lines: list[str]) -> list[dict]:
    user_prompt = (
        f"## Profil firmy\n\n{company_profile_text}\n\n"
        f"## Przetargi do oceny ({len(tender_lines)} szt.)\n\n"
        + "\n".join(tender_lines)
    )

    client = get_openai_client()
    response = client.chat.completions.create(
        model=settings.llm_model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": MATCHING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    result = json.loads(response.choices[0].message.content)  # type: ignore[arg-type]
    return result["matches"]


async def _save_matches_to_mongo(company_name: str, matches: list[dict]) -> None:
    db = get_database()
    collection = db[COLLECTION_NAME]

    bulk_ops = [
        ReplaceOne(
            {
                "_id": f"{company_name}::{match['tender_name']}::{match['organization']}",
            },
            {
                "_id": f"{company_name}::{match['tender_name']}::{match['organization']}",
                "company_name": company_name,
                "tender_name": match["tender_name"],
                "organization": match["organization"],
                "total_score": match["total_score"],
                "criteria": match["criteria"],
                "reasoning": match["reasoning"],
            },
            upsert=True,
        )
        for match in matches
    ]

    if bulk_ops:
        await collection.bulk_write(bulk_ops)
        logger.info(
            "Saved %d tender matches to MongoDB for %s", len(bulk_ops), company_name
        )


async def match_company_to_tenders(company_name: str) -> MatchCompanyResponse:
    company_profile_text = await _load_company_profile_text(company_name)
    tenders = _load_tenders()

    tender_lines: list[str] = []
    for t in tenders:
        name = t["metadata"]["name"]
        org = t["metadata"]["organization"]
        tender_lines.append(f"- Przetarg: {name} | Organizacja: {org}")

    batch_size = math.ceil(len(tender_lines) / BATCH_COUNT)
    all_matches: list[dict] = []

    for i in range(0, len(tender_lines), batch_size):
        chunk = tender_lines[i : i + batch_size]
        batch_num = i // batch_size + 1
        logger.info(
            "Scoring batch %d/%d (%d tenders) for %s",
            batch_num,
            BATCH_COUNT,
            len(chunk),
            company_name,
        )
        matches = await run_in_threadpool(_classify_batch, company_profile_text, chunk)
        all_matches.extend(matches)
        await _save_matches_to_mongo(company_name, matches)

    all_matches.sort(key=lambda x: -x["total_score"])

    return MatchCompanyResponse(
        company_name=company_name,
        matches=all_matches,
    )
