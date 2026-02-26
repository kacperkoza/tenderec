import json
import logging
from datetime import date
from functools import lru_cache

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from src.constants import TENDERS_PATH
from src.tenders.tender_constants import TENDER_AGENT_SYSTEM_PROMPT
from src.tenders.tender_schemas import Tender, TenderMetadata

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_tenders() -> list[Tender]:
    with open(TENDERS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [
        Tender(
            tender_url=t["tender_url"],
            metadata=TenderMetadata(**t["metadata"]),
            files_count=t["files_count"],
            file_urls=t["file_urls"],
        )
        for t in data["tenders"]
    ]


def _get_tender_by_name(name: str) -> Tender | None:
    for tender in _load_tenders():
        if tender.metadata.name == name:
            return tender
    return None


def _format_tender(tender: Tender) -> str:
    return (
        f"Name: {tender.metadata.name}\n"
        f"Organization: {tender.metadata.organization}\n"
        f"Submission deadline: {tender.metadata.submission_deadline}\n"
        f"Initiation date: {tender.metadata.initiation_date}\n"
        f"Procedure type: {tender.metadata.procedure_type or 'N/A'}\n"
        f"Source type: {tender.metadata.source_type or 'N/A'}\n"
        f"Tender URL: {tender.tender_url}\n"
        f"Files count: {tender.files_count}\n"
        f"File URLs: {', '.join(tender.file_urls) if tender.file_urls else 'None'}"
    )


@tool
def get_tender_details(tender_name: str) -> str:
    """Look up full details of a tender by its exact name.
    Returns name, organization, deadlines, dates, procedure type, file URLs, etc.
    """
    tender = _get_tender_by_name(tender_name)
    if tender is None:
        return f"Tender '{tender_name}' not found."
    return _format_tender(tender)


@tool
def search_tenders(query: str) -> str:
    """Search for tenders whose name contains the given query (case-insensitive).
    Returns a list of matching tender names with their organizations.
    Use this when the user provides a partial or approximate tender name.
    """
    query_lower = query.lower()
    matches = [t for t in _load_tenders() if query_lower in t.metadata.name.lower()]
    if not matches:
        return f"No tenders found matching '{query}'."

    results = [
        f"- {t.metadata.name} (org: {t.metadata.organization})" for t in matches[:20]
    ]
    header = f"Found {len(matches)} tender(s)"
    if len(matches) > 20:
        header += f" (showing first 20 of {len(matches)})"
    return header + ":\n" + "\n".join(results)


@tool
def list_tenders_by_organization(organization: str) -> str:
    """List all tenders from a given organization (case-insensitive partial match).
    Returns tender names and deadlines.
    """
    org_lower = organization.lower()
    matches = [
        t for t in _load_tenders() if org_lower in t.metadata.organization.lower()
    ]
    if not matches:
        return f"No tenders found for organization matching '{organization}'."

    results = [
        f"- {t.metadata.name} (deadline: {t.metadata.submission_deadline})"
        for t in matches[:20]
    ]
    header = f"Found {len(matches)} tender(s) for '{organization}'"
    if len(matches) > 20:
        header += f" (showing first 20 of {len(matches)})"
    return header + ":\n" + "\n".join(results)


@tool
def get_tender_files(tender_name: str) -> str:
    """Get the list of attached file URLs for a specific tender by its exact name."""
    tender = _get_tender_by_name(tender_name)
    if tender is None:
        return f"Tender '{tender_name}' not found."

    if not tender.file_urls:
        return f"Tender '{tender_name}' has no attached files."

    files = "\n".join(f"- {url}" for url in tender.file_urls)
    return f"Tender '{tender_name}' has {tender.files_count} file(s):\n{files}"


@tool
def get_today_date() -> str:
    """Get today's date. Useful for comparing against tender deadlines."""
    return str(date.today())


AGENT_TOOLS = [
    get_tender_details,
    search_tenders,
    list_tenders_by_organization,
    get_tender_files,
    get_today_date,
]


class TenderService:
    def __init__(self, llm_client: ChatOpenAI) -> None:
        self.agent = create_react_agent(
            model=llm_client,
            tools=AGENT_TOOLS,
            prompt=TENDER_AGENT_SYSTEM_PROMPT,
        )

    @staticmethod
    def load_tenders() -> list[Tender]:
        return _load_tenders()

    @staticmethod
    def get_tender_by_name(name: str) -> Tender | None:
        return _get_tender_by_name(name)

    async def ask_question(self, tender_name: str, question: str) -> str:
        tender = _get_tender_by_name(tender_name)
        if tender is None:
            raise ValueError(f"Tender not found: {tender_name}")

        user_message = (
            f'The user is asking about the tender named: "{tender_name}"\n\n'
            f"Question: {question}"
        )

        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": user_message}]}
        )

        ai_messages = [m for m in result["messages"] if m.type == "ai" and m.content]
        if not ai_messages:
            return "Unable to generate an answer."

        return ai_messages[-1].content  # type: ignore[return-value]


class _TenderServiceCompat:
    """Lightweight accessor for tender data without LLM dependency.
    Used by other services (e.g. recommendations) that only need data lookups.
    """

    @staticmethod
    def load_tenders() -> list[Tender]:
        return _load_tenders()

    @staticmethod
    def get_tender_by_name(name: str) -> Tender | None:
        return _get_tender_by_name(name)


tender_service = _TenderServiceCompat()
