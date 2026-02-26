from dataclasses import dataclass
from datetime import date, datetime

from pydantic import BaseModel


@dataclass
class TenderMetadata:
    name: str
    organization: str
    submission_deadline: str
    initiation_date: str
    procedure_type: str | None = None
    source_type: str = ""

    @property
    def deadline_date(self) -> date:
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(self.submission_deadline, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Invalid deadline format: {self.submission_deadline}")


@dataclass
class Tender:
    tender_url: str
    metadata: TenderMetadata
    files_count: int
    file_urls: list[str]


class TenderResponse(BaseModel):
    tender_url: str
    name: str
    organization: str
    submission_deadline: str
    initiation_date: str
    procedure_type: str | None = None
    source_type: str
    files_count: int
    file_urls: list[str]


class TenderQuestionRequest(BaseModel):
    tender_name: str
    question: str


class TenderQuestionResponse(BaseModel):
    tender_name: str
    question: str
    answer: str
