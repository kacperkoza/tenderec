from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


SAMPLE_FEEDBACK_DOC = {
    "_id": "feedback-uuid-1",
    "company": "testcorp",
    "comment": "Bardzo dobra firma, polecam.",
    "created_at": datetime(2026, 2, 20, 10, 0, 0, tzinfo=timezone.utc),
}

SAMPLE_FEEDBACK_DOC_2 = {
    "_id": "feedback-uuid-2",
    "company": "testcorp",
    "comment": "Szybka realizacja zamówień.",
    "created_at": datetime(2026, 2, 21, 12, 0, 0, tzinfo=timezone.utc),
}


def _mock_cursor(documents: list[dict]) -> MagicMock:
    cursor = MagicMock()
    cursor.sort = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=documents)
    return cursor


def _mock_collection(
    documents: list[dict] | None = None,
) -> MagicMock:
    collection = MagicMock()
    cursor = _mock_cursor(documents or [])
    collection.find = MagicMock(return_value=cursor)
    collection.insert_one = AsyncMock()
    return collection


def _mock_db(collection: MagicMock) -> MagicMock:
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=collection)
    return db


@pytest.fixture
def mock_mongo_empty():
    collection = _mock_collection([])
    db = _mock_db(collection)
    with patch("src.database._db", db):
        yield collection


@pytest.fixture
def mock_mongo_with_feedbacks():
    collection = _mock_collection([SAMPLE_FEEDBACK_DOC_2, SAMPLE_FEEDBACK_DOC])
    db = _mock_db(collection)
    with patch("src.database._db", db):
        yield collection


class TestGetFeedbacks:
    async def test_returns_empty_list(
        self, client: AsyncClient, mock_mongo_empty: MagicMock
    ):
        resp = await client.get("/api/v1/feedback/testcorp")

        assert resp.status_code == 200
        data = resp.json()
        assert data["company"] == "testcorp"
        assert data["feedbacks"] == []

    async def test_returns_feedbacks(
        self, client: AsyncClient, mock_mongo_with_feedbacks: MagicMock
    ):
        resp = await client.get("/api/v1/feedback/testcorp")

        assert resp.status_code == 200
        data = resp.json()
        assert data["company"] == "testcorp"
        assert len(data["feedbacks"]) == 2
        assert data["feedbacks"][0]["id"] == "feedback-uuid-2"
        assert data["feedbacks"][0]["comment"] == "Szybka realizacja zamówień."
        assert data["feedbacks"][1]["id"] == "feedback-uuid-1"


class TestCreateFeedback:
    async def test_creates_feedback(
        self, client: AsyncClient, mock_mongo_empty: MagicMock
    ):
        resp = await client.post(
            "/api/v1/feedback/testcorp",
            json={"comment": "Świetna firma!"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["comment"] == "Świetna firma!"
        assert "id" in data
        mock_mongo_empty.insert_one.assert_awaited_once()

    async def test_rejects_empty_comment(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/feedback/testcorp",
            json={"comment": ""},
        )

        assert resp.status_code == 422

    async def test_rejects_missing_comment(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/feedback/testcorp",
            json={},
        )

        assert resp.status_code == 422
