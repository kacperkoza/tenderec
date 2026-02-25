import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


SAMPLE_PROFILE = {
    "company_info": {
        "name": "TestCorp Sp. z o.o.",
        "industries": ["Utrzymanie zieleni", "Leśnictwo"],
    },
    "matching_criteria": {
        "service_categories": ["Koszenie trawników", "Wycinka drzew"],
        "cpv_codes": ["77310000-6"],
        "target_authorities": ["Gminy", "Zarządy Dróg"],
        "geography": {"primary_country": "Polska"},
    },
}

SAMPLE_DOCUMENT = {
    "_id": "testcorp",
    "profile": SAMPLE_PROFILE,
    "created_at": datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
}


def _mock_collection() -> MagicMock:
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=SAMPLE_DOCUMENT)
    collection.replace_one = AsyncMock()
    return collection


def _mock_db(collection: MagicMock) -> MagicMock:
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=collection)
    return db


def _mock_llm_response(content: dict) -> MagicMock:
    message = MagicMock()
    message.content = json.dumps(content)
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.fixture
def mock_mongo():
    collection = _mock_collection()
    db = _mock_db(collection)
    with patch("src.database._db", db):
        yield collection


@pytest.fixture
def mock_llm():
    client = MagicMock()
    with patch("src.llm.service._client", client):
        yield client


class TestGetCompanyProfile:
    async def test_returns_profile(self, client: AsyncClient, mock_mongo: MagicMock):
        resp = await client.get("/api/v1/companies/testcorp")

        assert resp.status_code == 200
        data = resp.json()
        assert data["company_name"] == "testcorp"
        assert data["profile"]["company_info"]["name"] == "TestCorp Sp. z o.o."
        assert len(data["profile"]["matching_criteria"]["cpv_codes"]) == 1

    async def test_not_found(self, client: AsyncClient, mock_mongo: MagicMock):
        mock_mongo.find_one = AsyncMock(return_value=None)

        resp = await client.get("/api/v1/companies/nonexistent")

        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


class TestUpsertCompanyProfile:
    async def test_creates_profile(
        self,
        client: AsyncClient,
        mock_mongo: MagicMock,
        mock_llm: MagicMock,
    ):
        mock_llm.chat.completions.create.return_value = _mock_llm_response(
            SAMPLE_PROFILE
        )

        resp = await client.put(
            "/api/v1/companies/testcorp",
            json={"description": "TestCorp zajmuje się utrzymaniem zieleni miejskiej."},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["company_name"] == "testcorp"
        assert data["profile"]["company_info"]["name"] == "TestCorp Sp. z o.o."
        mock_mongo.replace_one.assert_awaited_once()

    async def test_rejects_empty_description(self, client: AsyncClient):
        resp = await client.put(
            "/api/v1/companies/testcorp",
            json={"description": ""},
        )

        assert resp.status_code == 422
