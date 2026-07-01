from fastapi import APIRouter, HTTPException, status

from app.schemas.legal import LegalDocumentDetail, LegalDocumentListItem
from app.services.legal_document_service import LegalDocumentService


router = APIRouter(
    prefix="/legal",
    tags=["legal"],
)


def _service() -> LegalDocumentService:
    return LegalDocumentService()


def _list_item(document) -> LegalDocumentListItem:
    return LegalDocumentListItem(
        code=document.code,
        title=document.title,
        version=document.version,
        effective_from=document.effective_from,
        required=document.required,
        revocable=document.revocable,
        informational=document.informational,
    )


def _detail(document, service: LegalDocumentService) -> LegalDocumentDetail:
    return LegalDocumentDetail(
        **_list_item(document).model_dump(),
        content=service.read_document_content(document),
    )


@router.get("/documents", response_model=list[LegalDocumentListItem])
def list_documents():
    return [_list_item(document) for document in _service().list_active_documents()]


@router.get("/documents/{document_code}", response_model=LegalDocumentDetail)
def get_document(document_code: str):
    service = _service()
    document = service.get_active_document(document_code)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Legal document not found",
        )

    return _detail(document, service)


@router.get("/documents/{document_code}/versions/{version}", response_model=LegalDocumentDetail)
def get_document_version(document_code: str, version: str):
    service = _service()
    document = service.get_document_version(document_code, version)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Legal document version not found",
        )

    return _detail(document, service)
