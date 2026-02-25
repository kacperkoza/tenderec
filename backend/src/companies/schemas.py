from pydantic import BaseModel


class CompanyResponse(BaseModel):
    id: str
    description: str

