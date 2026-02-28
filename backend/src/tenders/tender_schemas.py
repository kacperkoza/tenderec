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

    @classmethod
    def from_json(cls, data: dict) -> "Tender":
        return cls(
            tender_url=data["tender_url"],
            metadata=TenderMetadata(**data["metadata"]),
            files_count=data["files_count"],
            file_urls=data["file_urls"],
        )

    def to_response(self) -> "TenderResponse":
        return TenderResponse(
            tender_url=self.tender_url,
            name=self.metadata.name,
            organization=self.metadata.organization,
            submission_deadline=self.metadata.submission_deadline,
            initiation_date=self.metadata.initiation_date,
            procedure_type=self.metadata.procedure_type,
            source_type=self.metadata.source_type,
            files_count=self.files_count,
            file_urls=self.file_urls,
        )


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
    company_name: str


class TenderQuestionResponse(BaseModel):
    tender_name: str
    question: str
    answer: str
