import asyncio
import io
import json
import logging
from datetime import date
from functools import lru_cache
from urllib.parse import unquote, urlparse

import httpx
from langchain_core.tools import BaseTool, tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from src.constants import TENDERS_PATH
from src.companies.company_service import CompanyService
from src.tenders.tender_constants import (
    MAX_EXTRACTED_TEXT_CHARS,
    MAX_FILE_SIZE_BYTES,
    SUPPORTED_FILE_EXTENSIONS,
    TENDER_AGENT_SYSTEM_PROMPT,
)
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


def _get_file_extension(url: str) -> str:
    """Extract lowercase file extension from a URL path."""
    path = unquote(urlparse(url).path)
    dot_index = path.rfind(".")
    if dot_index == -1:
        return ""
    return path[dot_index:].lower()


def _extract_text_from_pdf(content: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def _extract_text_from_docx(content: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _extract_text_from_txt(content: bytes) -> str:
    for encoding in ("utf-8", "cp1250", "latin-1"):
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, ValueError):
            continue
    return content.decode("utf-8", errors="replace")


def _extract_text(content: bytes, extension: str) -> str:
    if extension == ".pdf":
        return _extract_text_from_pdf(content)
    if extension == ".docx":
        return _extract_text_from_docx(content)
    if extension == ".txt":
        return _extract_text_from_txt(content)
    return f"Unsupported file format: {extension}"


@tool
async def read_file_content(file_url: str) -> str:
    """Download a tender file from its URL and extract the text content.
    Use this when the user asks about the contents of a specific tender document.
    Supports PDF, DOCX, and TXT files. First call get_tender_files to get file URLs,
    then use this tool with one of those URLs.
    """
    extension = _get_file_extension(file_url)
    if extension not in SUPPORTED_FILE_EXTENSIONS:
        return (
            f"Cannot read file with extension '{extension}'. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_FILE_EXTENSIONS))}."
        )

    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(file_url)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return f"Failed to download file: HTTP {exc.response.status_code}"
    except httpx.RequestError as exc:
        return f"Failed to download file: {exc}"

    if len(response.content) > MAX_FILE_SIZE_BYTES:
        size_mb = len(response.content) / (1024 * 1024)
        return f"File too large ({size_mb:.1f} MB). Maximum supported size is {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."

    try:
        text = await asyncio.to_thread(_extract_text, response.content, extension)
    except Exception as exc:
        logger.exception("Failed to extract text from %s", file_url)
        return f"Failed to extract text from file: {exc}"

    if not text.strip():
        return "The file appears to be empty or contains no extractable text (e.g., scanned image PDF)."

    if len(text) > MAX_EXTRACTED_TEXT_CHARS:
        text = (
            text[:MAX_EXTRACTED_TEXT_CHARS]
            + "\n\n[... content truncated due to length ...]"
        )

    return text


AGENT_TOOLS = [
    get_tender_details,
    search_tenders,
    list_tenders_by_organization,
    get_tender_files,
    get_today_date,
    read_file_content,
]


def _build_company_tool(company_service: CompanyService) -> BaseTool:
    @tool
    async def get_company_info(company_name: str) -> str:
        """Get the profile of the user's company from the database.
        Returns company name, industries, service categories, CPV codes,
        target authorities, and geography. Use this when the user asks
        about their company, wants to compare a tender to their profile,
        or asks whether a tender is relevant for them.
        """
        profile_response = await company_service.get_company(company_name)
        if profile_response is None:
            return f"Company '{company_name}' not found in the database."

        profile = profile_response.profile
        info = profile.company_info
        criteria = profile.matching_criteria

        return (
            f"Company: {info.name}\n"
            f"Industries: {', '.join(info.industries)}\n"
            f"Service categories: {', '.join(criteria.service_categories)}\n"
            f"CPV codes: {', '.join(criteria.cpv_codes)}\n"
            f"Target authorities: {', '.join(criteria.target_authorities)}\n"
            f"Geography: {criteria.geography.primary_country}"
        )

    return get_company_info  # type: ignore[return-value]


class TenderService:
    def __init__(
        self,
        llm_client: ChatOpenAI,
        company_service: CompanyService,
    ) -> None:
        tools = [*AGENT_TOOLS, _build_company_tool(company_service)]
        self.agent = create_react_agent(
            model=llm_client,
            tools=tools,
            prompt=TENDER_AGENT_SYSTEM_PROMPT,
        )

    @staticmethod
    def load_tenders() -> list[Tender]:
        return _load_tenders()

    @staticmethod
    def get_tender_by_name(name: str) -> Tender | None:
        return _get_tender_by_name(name)

    async def ask_question(
        self, tender_name: str, question: str, company_name: str
    ) -> str:
        tender = _get_tender_by_name(tender_name)
        if tender is None:
            raise ValueError(f"Tender not found: {tender_name}")

        user_message = (
            f'The user is asking about the tender named: "{tender_name}"\n'
            f'The user\'s company name is: "{company_name}"\n\n'
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
