import html
import json
from dataclasses import dataclass
from pathlib import Path


LEGAL_ROOT = Path(__file__).resolve().parents[2] / "legal"


@dataclass(frozen=True)
class LegalDocument:
    code: str
    title: str
    version: str
    effective_from: str
    file: str
    required: bool
    revocable: bool
    informational: bool


class LegalDocumentService:
    def __init__(self, legal_root: Path = LEGAL_ROOT):
        self.legal_root = legal_root

    def list_active_documents(self) -> list[LegalDocument]:
        return [LegalDocument(**item) for item in self._load_manifest()]

    def get_active_document(self, code: str) -> LegalDocument | None:
        return next((document for document in self.list_active_documents() if document.code == code), None)

    def get_document_version(self, code: str, version: str) -> LegalDocument | None:
        active = self.get_active_document(code)

        if active is not None and active.version == version:
            return active

        document_dir = self._document_dir_for_code(code)
        if document_dir is None:
            return None

        file_path = document_dir / f"{version}.md"
        if not file_path.exists():
            return None

        if active is None:
            return None

        return LegalDocument(
            code=active.code,
            title=active.title,
            version=version,
            effective_from=version,
            file=str(file_path.relative_to(self.legal_root)).replace("\\", "/"),
            required=active.required,
            revocable=active.revocable,
            informational=active.informational,
        )

    def read_document_content(self, document: LegalDocument) -> str:
        path = (self.legal_root / document.file).resolve()
        root = self.legal_root.resolve()

        if root not in path.parents:
            raise ValueError("Legal document path escapes legal root")

        content = path.read_text(encoding="utf-8")
        return html.escape(content, quote=False)

    def require_current_version(self, code: str, version: str) -> LegalDocument:
        document = self.get_active_document(code)

        if document is None or document.version != version:
            raise ValueError(f"Document {code} version {version} is not current")

        return document

    def _load_manifest(self) -> list[dict]:
        manifest_path = self.legal_root / "manifest.json"
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def _document_dir_for_code(self, code: str) -> Path | None:
        active = self.get_active_document(code)

        if active is None:
            return None

        return self.legal_root / Path(active.file).parent
