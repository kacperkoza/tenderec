import json
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


SAMPLE_CLASSIFICATIONS = [
    {
        "_id": "Gmina Kraków",
        "industries": [
            {"industry": "Administracja samorządowa", "reasoning": "Gmina miejska."},
            {"industry": "Infrastruktura miejska", "reasoning": "Przetargi na drogi."},
        ],
    },
    {
        "_id": "PKP Intercity S.A.",
        "industries": [
            {"industry": "Transport kolejowy", "reasoning": "Przewozy pasażerskie."},
        ],
    },
]


def _mock_cursor(docs: list[dict]) -> MagicMock:
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=docs)
    return cursor


def _mock_collection(docs: list[dict]) -> MagicMock:
    collection = MagicMock()
    collection.find = MagicMock(return_value=_mock_cursor(docs))
    collection.bulk_write = AsyncMock()
    return collection


def _mock_db(collection: MagicMock) -> MagicMock:
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=collection)
    return db


@pytest.fixture
def mock_mongo_with_data():
    collection = _mock_collection(SAMPLE_CLASSIFICATIONS)
    db = _mock_db(collection)
    with patch("src.database._db", db):
        yield collection


@pytest.fixture
def mock_mongo_empty():
    collection = _mock_collection([])
    db = _mock_db(collection)
    with patch("src.database._db", db):
        yield collection


class TestGetOrganizationIndustries:
    async def test_returns_cached_classifications(
        self, client: AsyncClient, mock_mongo_with_data: MagicMock
    ):
        resp = await client.get("/api/v1/organizations/industries")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["organizations"]) == 2
        assert data["organizations"][0]["organization"] == "Gmina Kraków"
        assert len(data["organizations"][0]["industries"]) == 2
        assert data["organizations"][1]["organization"] == "PKP Intercity S.A."

    async def test_returns_empty_when_no_data(
        self, client: AsyncClient, mock_mongo_empty: MagicMock
    ):
        resp = await client.get("/api/v1/organizations/industries")

        assert resp.status_code == 200
        data = resp.json()
        assert data["organizations"] == []

    async def test_llm_source_classifies_and_saves(
        self, client: AsyncClient, mock_mongo_with_data: MagicMock
    ):
        llm_response_content = {
            "organizations": [
                {
                    "organization": "Test Org",
                    "industries": [
                        {
                            "industry": "Energetyka",
                            "reasoning": "Przetargi na energię.",
                        },
                        {"industry": "Przemysł", "reasoning": "Zakłady przemysłowe."},
                    ],
                }
            ]
        }

        mock_llm = MagicMock()
        message = MagicMock()
        message.content = json.dumps(llm_response_content)
        choice = MagicMock()
        choice.message = message
        response = MagicMock()
        response.choices = [choice]
        mock_llm.chat.completions.create.return_value = response

        with (
            patch("src.config.settings.organization_classification_source", "llm"),
            patch("src.llm.service._client", mock_llm),
            patch(
                "src.organization_classification.service._load_tenders",
                return_value=[
                    {
                        "metadata": {
                            "name": "Dostawa energii",
                            "organization": "Test Org",
                            "submission_deadline": "2026-02-01 12:00",
                        }
                    }
                ],
            ),
            patch(
                "src.organization_classification.constants.get_deadline_reference_date",
                return_value=date(2026, 1, 10),
            ),
        ):
            resp = await client.get("/api/v1/organizations/industries")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["organizations"]) == 1
        assert data["organizations"][0]["organization"] == "Test Org"
        mock_mongo_with_data.bulk_write.assert_awaited_once()
