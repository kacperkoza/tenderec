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

BATCH_SIZE = 80

SYSTEM_PROMPT = """\
Jesteś ekspertem od polskiego rynku zamówień publicznych i klasyfikacji branżowej organizacji.

Dostajesz listę organizacji pogrupowanych wg nazwy. Przy każdej organizacji podane są \
nazwy przetargów, które ta organizacja ogłosiła.

Twoim zadaniem jest:
1. Na podstawie nazwy organizacji i nazw jej przetargów — przypisz każdą organizację \
do 2 lub 3 branż (top branże, od najbardziej pasującej).
Pierwsza (najważniejsza) branża niech bazuje na nazwie organizacji, a kolejne branże niech bazują na nazwie organizacji i nazwach przetargów.
2. Dla KAŻDEJ przypisanej branży dodaj krótkie uzasadnienie po polsku (1-2 zdania), \
dlaczego ta branża pasuje — odnieś się do konkretnych przetargów.
3. Użyj zwięzłych, polskich nazw branż (np. "Energetyka", "Górnictwo", \
"Administracja samorządowa", "Transport kolejowy", "Przemysł chemiczny" itp.).
4. Pierwsza branża na liście = najbardziej trafna.

Odpowiedz WYŁĄCZNIE poprawnym JSON-em w formacie:
{
  "organizations": [
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


def _build_user_prompt(org_batch: dict[str, list[str]]) -> str:
    lines: list[str] = []
    for org, names in org_batch.items():
        tender_list = "; ".join(names)
        lines.append(f"- {org}: {tender_list}")

    return f"Oto {len(lines)} organizacji z ich przetargami:\n\n" + "\n".join(lines)


def _classify_batch(org_batch: dict[str, list[str]]) -> list[dict]:
    client = get_openai_client()
    user_prompt = _build_user_prompt(org_batch)

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
    result = json.loads(raw)  # type: ignore[arg-type]
    return result["organizations"]


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

    org_names = list(grouped.keys())
    all_organizations: list[dict] = []

    for i in range(0, len(org_names), BATCH_SIZE):
        batch_keys = org_names[i : i + BATCH_SIZE]
        batch = {org: grouped[org] for org in batch_keys}
        logger.info(
            "Classifying batch %d-%d of %d organizations",
            i + 1,
            min(i + BATCH_SIZE, len(org_names)),
            len(org_names),
        )
        classified = await run_in_threadpool(_classify_batch, batch)
        all_organizations.extend(classified)

    await _save_to_mongo(all_organizations)
    return ClassifyResponse(organizations=all_organizations)


async def get_industries() -> ClassifyResponse:
    source = settings.organization_classification_source

    if source == "mongodb":
        return await _load_from_mongo()
    return await _classify_via_llm()
