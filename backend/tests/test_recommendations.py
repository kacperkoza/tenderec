import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


SAMPLE_PROFILE_DOC = {
    "_id": "greenworks",
    "profile": {
        "company_info": {
            "name": "GreenWorks Sp. z o.o.",
            "industries": ["Utrzymanie zieleni"],
        },
        "matching_criteria": {
            "service_categories": ["Koszenie trawników"],
            "cpv_codes": ["77310000-6"],
            "target_authorities": ["Gminy"],
            "geography": {"primary_country": "Polska"},
        },
    },
    "created_at": datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
}

SAMPLE_LLM_MATCH_RESPONSE = {
    "matches": [
        {
            "tender_name": "Utrzymanie zieleni w gminie",
            "organization": "Gmina Kraków",
            "total_score": 85,
            "criteria": {
                "subject_match": {
                    "score": 45,
                    "reasoning": "Bezpośrednie dopasowanie.",
                },
                "service_vs_delivery": {"score": 25, "reasoning": "Czysta usługa."},
                "authority_profile": {
                    "score": 15,
                    "reasoning": "Gmina - idealny klient.",
                },
            },
            "reasoning": "Bardzo dobre dopasowanie do profilu firmy.",
        }
    ]
}

SAMPLE_TENDERS = {
    "tenders": [
        {
            "metadata": {
                "name": "Utrzymanie zieleni w gminie",
                "organization": "Gmina Kraków",
                "submission_deadline": "2026-03-01 12:00",
            }
        }
    ]
}


def _mock_find_one_side_effect(filter_dict: dict) -> dict | None:
    if filter_dict.get("_id") == "greenworks":
        return SAMPLE_PROFILE_DOC
    return None


def _mock_collection() -> MagicMock:
    collection = MagicMock()
    collection.find_one = AsyncMock(side_effect=_mock_find_one_side_effect)
    collection.replace_one = AsyncMock()
    collection.bulk_write = AsyncMock()
    return collection


def _mock_db(collection: MagicMock) -> MagicMock:
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=collection)
    return db


@pytest.fixture
def mock_mongo():
    collection = _mock_collection()
    db = _mock_db(collection)
    with patch("src.database._db", db):
        yield collection


@pytest.fixture
def mock_llm():
    mock_client = MagicMock()
    message = MagicMock()
    message.content = json.dumps(SAMPLE_LLM_MATCH_RESPONSE)
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    mock_client.chat.completions.create.return_value = response
    with patch("src.llm.service._client", mock_client):
        yield mock_client


@pytest.fixture
def mock_tenders():
    with patch(
        "src.recommendations.service._load_tenders",
        return_value=SAMPLE_TENDERS["tenders"],
    ):
        yield


class TestMatchCompany:
    async def test_matches_default_company(
        self,
        client: AsyncClient,
        mock_mongo: MagicMock,
        mock_llm: MagicMock,
        mock_tenders: None,
    ):
        resp = await client.post("/api/v1/recommendations/match")

        assert resp.status_code == 200
        data = resp.json()
        assert data["company_name"] == "greenworks"
        assert len(data["matches"]) == 1
        match = data["matches"][0]
        assert match["tender_name"] == "Utrzymanie zieleni w gminie"
        assert match["organization"] == "Gmina Kraków"
        assert match["total_score"] == 85
        assert match["criteria"]["subject_match"]["score"] == 45

    async def test_matches_custom_company(
        self,
        client: AsyncClient,
        mock_mongo: MagicMock,
        mock_llm: MagicMock,
        mock_tenders: None,
    ):
        resp = await client.post(
            "/api/v1/recommendations/match?company_name=greenworks"
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["company_name"] == "greenworks"

    async def test_company_not_found(
        self,
        client: AsyncClient,
        mock_mongo: MagicMock,
    ):
        resp = await client.post(
            "/api/v1/recommendations/match?company_name=nonexistent"
        )

        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    async def test_saves_matches_to_mongo(
        self,
        client: AsyncClient,
        mock_mongo: MagicMock,
        mock_llm: MagicMock,
        mock_tenders: None,
    ):
        await client.post("/api/v1/recommendations/match")

        mock_mongo.bulk_write.assert_awaited()
