import logging
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.database import get_database
from src.feedback.feedback_constants import COLLECTION_NAME
from src.feedback.feedback_schemas import (
    FeedbackDocument,
    FeedbackListResponse,
    FeedbackResponse,
)

logger = logging.getLogger(__name__)


class FeedbackService:
    def __init__(self) -> None:
        self._db: AsyncIOMotorDatabase | None = None

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._db is None:
            self._db = get_database()
        return self._db

    async def get_feedbacks(self, company_name: str) -> FeedbackListResponse:
        collection = self.db[COLLECTION_NAME]

        cursor = collection.find({"company_name": company_name})
        documents = await cursor.to_list(length=None)

        feedbacks = [
            FeedbackDocument.from_mongo(doc).to_response() for doc in documents
        ]

        return FeedbackListResponse(company_name=company_name, feedbacks=feedbacks)

    async def create_feedback(
        self, company_name: str, feedback_comment: str
    ) -> FeedbackResponse:
        collection = self.db[COLLECTION_NAME]

        feedback_id = str(uuid.uuid4())
        document = FeedbackDocument(
            id=feedback_id,
            company_name=company_name,
            feedback_comment=feedback_comment,
        )

        await collection.insert_one(document.to_mongo())
        logger.info("Created feedback '%s' for company '%s'", feedback_id, company_name)

        return document.to_response()


feedback_service = FeedbackService()
