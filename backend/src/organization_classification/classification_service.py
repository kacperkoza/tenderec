import json
import logging
from collections import defaultdict

from fastapi.concurrency import run_in_threadpool
from motor.motor_asyncio import AsyncIOMotorDatabase
from openai import OpenAI

from src.config import settings
from src.database import get_database
from src.llm.llm_service import llm_service
from src.organization_classification import classification_constants as constants
from src.organization_classification.classification_schemas import ClassifyResponse

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


class ClassificationService:
    def __init__(self) -> None:
        self._db: AsyncIOMotorDatabase | None = None
        self._client: OpenAI | None = None

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._db is None:
            self._db = get_database()
        return self._db

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = llm_service.get_client()
        return self._client

    @staticmethod
    def _load_tenders() -> list[dict]:
        with open(constants.TENDERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)["tenders"]

    @staticmethod
    def _group_by_organization(tenders: list[dict]) -> dict[str, list[str]]:
        grouped: dict[str, set[str]] = defaultdict(set)
        for t in tenders:
            org = t["metadata"]["organization"]
            name = t["metadata"]["name"]
            grouped[org].add(name)
        return {org: sorted(names) for org, names in grouped.items()}

    @staticmethod
    def _build_user_prompt(org_name: str, tender_names: list[str]) -> str:
        tenders = "\n".join(f"- {name}" for name in tender_names)
        return f"## Organization: {org_name}\n\n### Tenders:\n{tenders}"

    def _classify_organization(self, org_name: str, tender_names: list[str]) -> dict:
        user_prompt = self._build_user_prompt(org_name, tender_names)

        response = self.client.chat.completions.create(
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

    async def _save_one_to_mongo(self, organization: dict) -> None:
        collection = self.db[constants.COLLECTION_NAME]

        doc = {
            "_id": organization["organization"],
            "industries": organization["industries"],
        }
        await collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)
        logger.info("Saved classification for '%s' to MongoDB", doc["_id"])

    async def _load_from_mongo(self) -> ClassifyResponse:
        collection = self.db[constants.COLLECTION_NAME]
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

    async def _classify_via_llm(self) -> ClassifyResponse:
        all_tenders = self._load_tenders()
        grouped = self._group_by_organization(all_tenders)

        for i, (org_name, tender_names) in enumerate(grouped.items(), 1):
            logger.info(
                "Classifying organization %d/%d: '%s' (%d tenders)",
                i,
                len(grouped),
                org_name,
                len(tender_names),
            )
            classified = await run_in_threadpool(
                self._classify_organization, org_name, tender_names
            )
            logger.info(
                "Result after classification: %s",
                json.dumps(classified, ensure_ascii=False),
            )
            await self._save_one_to_mongo(classified)

        return await self._load_from_mongo()

    async def get_industries(self) -> ClassifyResponse:
        source = settings.organization_classification_source

        if source == "mongodb":
            return await self._load_from_mongo()
        return await self._classify_via_llm()


classification_service = ClassificationService()
