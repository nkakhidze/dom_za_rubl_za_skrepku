import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getLegalDocument, LegalDocumentDetail } from "../api/client";


const ROUTE_TO_CODE: Record<string, string> = {
  "user-agreement": "user_agreement",
  "privacy-policy": "privacy_policy",
  "personal-data-consent": "personal_data_consent",
  "public-data-consent": "public_data_consent",
  "marketing-consent": "marketing_consent",
};


function renderMarkdown(content: string) {
  return content.split("\n").map((line, index) => {
    if (line.startsWith("# ")) {
      return <h2 key={index}>{line.slice(2)}</h2>;
    }

    if (line.startsWith("## ")) {
      return <h3 key={index}>{line.slice(3)}</h3>;
    }

    if (line.startsWith("- ")) {
      return <li key={index}>{line.slice(2)}</li>;
    }

    if (!line.trim()) {
      return <br key={index} />;
    }

    return <p key={index}>{line}</p>;
  });
}


export function LegalDocumentPage() {
  const { documentSlug } = useParams();
  const [document, setDocument] = useState<LegalDocumentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const code = documentSlug ? ROUTE_TO_CODE[documentSlug] : null;

  useEffect(() => {
    if (!code) {
      setError("Документ не найден.");
      return;
    }

    getLegalDocument(code)
      .then(setDocument)
      .catch((loadError) =>
        setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить документ."),
      );
  }, [code]);

  if (error) {
    return (
      <section className="form-section">
        <p className="notice error">{error}</p>
        <Link to="/register">Вернуться к регистрации</Link>
      </section>
    );
  }

  if (!document) {
    return <p>Загрузка документа...</p>;
  }

  return (
    <section className="form-section legal-document">
      <Link to="/register">← Вернуться к регистрации</Link>
      <h1>{document.title}</h1>
      <p className="muted">
        Редакция {document.version}, действует с {document.effective_from}
      </p>
      <div className="legal-content">{renderMarkdown(document.content)}</div>
    </section>
  );
}
