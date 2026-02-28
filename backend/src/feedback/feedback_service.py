import logging
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.feedback.feedback_constants import COLLECTION_NAME
from src.feedback.feedback_schemas import (
    FeedbackDocument,
    FeedbackListResponse,
    FeedbackResponse,
)

logger = logging.getLogger(__name__)


class FeedbackService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    async def get_feedbacks(self, company_name: str) -> FeedbackListResponse:
        logger.info("Loading feedbacks for company '%s'", company_name)
        collection = self.db[COLLECTION_NAME]

        cursor = collection.find({"company_name": company_name})
        documents = await cursor.to_list(length=None)

        feedbacks = [
            FeedbackDocument.from_mongo(doc).to_response() for doc in documents
        ]

        logger.info("Found %d feedbacks for company '%s'", len(feedbacks), company_name)
        return FeedbackListResponse(company_name=company_name, feedbacks=feedbacks)

    async def create_feedback(
        self, company_name: str, feedback_comment: str
    ) -> FeedbackResponse:
        logger.info("Creating feedback for company '%s'", company_name)
        collection = self.db[COLLECTION_NAME]

        feedback_id = str(uuid.uuid4())
        document = FeedbackDocument(
            id=feedback_id,
            company_name=company_name,
            feedback_comment=feedback_comment,
        )

        await collection.insert_one(document.to_mongo())
        logger.info(f"Created feedback '{feedback_id}' for company '{company_name}'")

        return document.to_response()
