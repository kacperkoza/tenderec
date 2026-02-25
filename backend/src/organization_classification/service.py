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
You are an expert in the Polish public procurement market and industry classification of organizations.

You receive an organization name and a list of tenders published by that organization.

Your task:
1. Assign the organization 1 to 3 industries (from most relevant to least).
- The first industry must be based EXCLUSIVELY on the organization name (ignore tenders).
- Additional industries (max 2) should only be added if the tenders indicate industries \
DIFFERENT from the first one. If the tenders align with the first industry, do not add more.
2. For EACH assigned industry, provide a short reasoning in Polish (1-2 sentences). \
For the first industry, refer to the organization name. For the rest, refer to specific tenders.
3. Use concise Polish industry names (e.g. "Energetyka", "Górnictwo", \
"Administracja samorządowa", "Transport kolejowy", "Przemysł chemiczny", etc.).
4. The first industry in the list = the most relevant one.

Respond ONLY with valid JSON in the following format:
{
  "organization": "<organization name>",
  "industries": [
    {
      "industry": "<industry 1 - best match>",
      "reasoning": "<reasoning in Polish>"
    },
    {
      "industry": "<industry 2>",
      "reasoning": "<reasoning in Polish>"
    }
  ]
}

Do not include any text outside of the JSON.\
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
    return f"## Organization: {org_name}\n\n### Tenders:\n{tenders}"


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
