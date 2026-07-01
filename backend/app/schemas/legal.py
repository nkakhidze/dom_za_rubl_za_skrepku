from pydantic import BaseModel


class LegalDocumentListItem(BaseModel):
    code: str
    title: str
    version: str
    effective_from: str
    required: bool
    revocable: bool
    informational: bool


class LegalDocumentDetail(LegalDocumentListItem):
    content: str
