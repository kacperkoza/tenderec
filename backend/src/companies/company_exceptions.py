class CompanyNotFound(Exception):
    def __init__(self, company_name: str) -> None:
        self.company_name = company_name
        super().__init__(f"Company not found: {company_name}")


class ProfileExtractionError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
