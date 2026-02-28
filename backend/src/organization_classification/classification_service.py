import json
import logging
from collections import defaultdict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.config import settings
from src.constants import TENDERS_PATH
from src.organization_classification.classification_constants import (
    CLASSIFICATION_SYSTEM_PROMPT,
    COLLECTION_NAME,
)
from src.organization_classification.classification_schemas import (
    ClassifyResponse,
    IndustryClassificationEntry,
    OrganizationClassificationData,
    OrganizationClassificationDocument,
)

logger = logging.getLogger(__name__)


class ClassificationService:
    def __init__(self, db: AsyncIOMotorDatabase, llm_client: ChatOpenAI) -> None:
        self.db = db
        self.llm_client = llm_client

    @staticmethod
    def _load_tenders() -> list[dict]:
        with open(TENDERS_PATH, "r", encoding="utf-8") as f:
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

    async def _classify_organization(
        self, org_name: str, tender_names: list[str]
    ) -> OrganizationClassificationData:
        logger.info(
            "Classifying organization '%s' with %d tenders", org_name, len(tender_names)
        )
        user_prompt = self._build_user_prompt(org_name, tender_names)

        response = await self.llm_client.ainvoke(
            [
                SystemMessage(content=CLASSIFICATION_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ],
            response_format={"type": "json_object"},
        )

        raw = json.loads(response.content)  # type: ignore[arg-type]
        return OrganizationClassificationData(
            organization=raw["organization"],
            industries=[
                IndustryClassificationEntry(**ind) for ind in raw["industries"]
            ],
        )

    async def _save_one_to_mongo(
        self, document: OrganizationClassificationDocument
    ) -> None:
        collection = self.db[COLLECTION_NAME]
        mongo_doc = document.to_mongo()
        await collection.replace_one({"_id": mongo_doc["_id"]}, mongo_doc, upsert=True)
        logger.info("Saved classification for '%s' to MongoDB", document.id)

    async def _load_from_mongo(self) -> ClassifyResponse:
        logger.info("Loading organization classifications from MongoDB")
        collection = self.db[COLLECTION_NAME]
        cursor = collection.find({})
        docs = await cursor.to_list(length=None)

        organizations = [
            OrganizationClassificationDocument.from_mongo(doc).to_response()
            for doc in docs
        ]
        logger.info(
            "Loaded %d organization classifications from MongoDB", len(organizations)
        )
        return ClassifyResponse(organizations=organizations)

    async def _classify_via_llm(self) -> ClassifyResponse:
        all_tenders = self._load_tenders()
        grouped = self._group_by_organization(all_tenders)

        for index, (org_name, tender_names) in enumerate(grouped.items(), 1):
            logger.info(
                "Classifying organization %d/%d: '%s' (%d tenders)",
                index,
                len(grouped),
                org_name,
                len(tender_names),
            )
            classified = await self._classify_organization(org_name, tender_names)
            logger.info(
                "Classification result for '%s': %s",
                org_name,
                [ind.industry for ind in classified.industries],
            )
            document = OrganizationClassificationDocument.from_domain(classified)
            await self._save_one_to_mongo(document)

        return await self._load_from_mongo()

    async def get_industries(self) -> ClassifyResponse:
        source = settings.organization_classification_source
        logger.info("Getting industries (source=%s)", source)

        if source == "mongodb":
            return await self._load_from_mongo()
        return await self._classify_via_llm()
