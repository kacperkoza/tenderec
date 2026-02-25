import json
import logging
from collections import defaultdict

from fastapi.concurrency import run_in_threadpool
from pymongo import ReplaceOne

from src.config import settings
from src.database import get_database
from src.llm.service import get_openai_client
from src.organization_classification import constants
from src.organization_classification.schemas import ClassifyResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Jesteś ekspertem od polskiego rynku zamówień publicznych i klasyfikacji branżowej organizacji.

Dostajesz nazwę organizacji oraz listę przetargów, które ta organizacja ogłosiła.

Twoim zadaniem jest:
1. Przypisz organizacji od 1 do 3 branż (od najbardziej pasującej).
- Pierwsza branża musi bazować WYŁĄCZNIE na nazwie organizacji (ignoruj przetargi).
- Kolejne branże (max 2) dodaj tylko jeśli przetargi wskazują na branże INNE niż pierwsza. \
Jeśli przetargi pokrywają się z pierwszą branżą, nie dodawaj kolejnych.
2. Dla KAŻDEJ przypisanej branży dodaj krótkie uzasadnienie po polsku (1-2 zdania). \
Dla pierwszej branży odnieś się do nazwy organizacji. Dla kolejnych — do konkretnych przetargów.
3. Użyj zwięzłych, polskich nazw branż (np. "Energetyka", "Górnictwo", \
"Administracja samorządowa", "Transport kolejowy", "Przemysł chemiczny" itp.).
4. Pierwsza branża na liście = najbardziej trafna.

Odpowiedz WYŁĄCZNIE poprawnym JSON-em w formacie:
{
  "organization": "<nazwa organizacji>",
  "industries": [
    {
      "industry": "<branża 1 - najlepsza>",
      "reasoning": "<uzasadnienie po polsku>"
    },
    {
      "industry": "<branża 2>",
      "reasoning": "<uzasadnienie po polsku>"
    }
  ]
}

Nie dodawaj żadnego tekstu poza JSON-em.\
"""


def _load_tenders() -> list[dict]:
    with open(constants.TENDERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["tenders"]


def _group_by_organization(tenders: list[dict]) -> dict[str, list[str]]:
    grouped: dict[str, set[str]] = defaultdict(set)
    for t in tenders:
        org = t["metadata"]["organization"]
        name = t["metadata"]["name"]
        grouped[org].add(name)
    return {org: sorted(names) for org, names in grouped.items()}


def _build_user_prompt(org_name: str, tender_names: list[str]) -> str:
    tenders = "\n".join(f"- {name}" for name in tender_names)
    return f"## Organizacja: {org_name}\n\n### Przetargi:\n{tenders}"


def _classify_organization(org_name: str, tender_names: list[str]) -> dict:
    client = get_openai_client()
    user_prompt = _build_user_prompt(org_name, tender_names)

    response = client.chat.completions.create(
        model=settings.llm_model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content
    return json.loads(raw)  # type: ignore[arg-type]


async def _save_to_mongo(organizations: list[dict]) -> None:
    db = get_database()
    collection = db[constants.COLLECTION_NAME]

    operations = []
    for org in organizations:
        doc = {
            "_id": org["organization"],
            "industries": org["industries"],
        }
        operations.append(doc)

    if operations:
        bulk_ops = [
            ReplaceOne({"_id": doc["_id"]}, doc, upsert=True) for doc in operations
        ]
        await collection.bulk_write(bulk_ops)
        logger.info("Saved %d organization classifications to MongoDB", len(operations))


async def _load_from_mongo() -> ClassifyResponse:
    db = get_database()
    collection = db[constants.COLLECTION_NAME]
    cursor = collection.find({})
    docs = await cursor.to_list(length=None)

    organizations = [
        {
            "organization": doc["_id"],
            "industries": doc["industries"],
        }
        for doc in docs
    ]
    return ClassifyResponse(organizations=organizations)


async def _classify_via_llm() -> ClassifyResponse:
    all_tenders = _load_tenders()
    grouped = _group_by_organization(all_tenders)

    all_organizations: list[dict] = []

    for i, (org_name, tender_names) in enumerate(grouped.items(), 1):
        logger.info(
            "Classifying organization %d/%d: '%s' (%d tenders)",
            i,
            len(grouped),
            org_name,
            len(tender_names),
        )
        classified = await run_in_threadpool(
            _classify_organization, org_name, tender_names
        )
        logger.info(
            "Result after classification: %s",
            json.dumps(classified, ensure_ascii=False),
        )
        all_organizations.append(classified)

    await _save_to_mongo(all_organizations)
    return ClassifyResponse(organizations=all_organizations)


async def get_industries() -> ClassifyResponse:
    source = settings.organization_classification_source

    if source == "mongodb":
        return await _load_from_mongo()
    return await _classify_via_llm()
