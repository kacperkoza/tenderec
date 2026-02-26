import logging
import uuid

from src.database import get_database
from src.feedback.constants import COLLECTION_NAME
from src.feedback.schemas import (
    FeedbackDocument,
    FeedbackListResponse,
    FeedbackResponse,
)

logger = logging.getLogger(__name__)


async def get_feedbacks(company_name: str) -> FeedbackListResponse:
    db = get_database()
    collection = db[COLLECTION_NAME]

    cursor = collection.find({"company_name": company_name})
    documents = await cursor.to_list(length=None)

    feedbacks = [FeedbackDocument.from_mongo(doc).to_response() for doc in documents]

    return FeedbackListResponse(company_name=company_name, feedbacks=feedbacks)


async def create_feedback(company_name: str, feedback_comment: str) -> FeedbackResponse:
    db = get_database()
    collection = db[COLLECTION_NAME]

    feedback_id = str(uuid.uuid4())
    document = FeedbackDocument(
        id=feedback_id,
        company_name=company_name,
        feedback_comment=feedback_comment,
    )

    await collection.insert_one(document.to_mongo())
    logger.info("Created feedback '%s' for company '%s'", feedback_id, company_name)

    return document.to_response()
