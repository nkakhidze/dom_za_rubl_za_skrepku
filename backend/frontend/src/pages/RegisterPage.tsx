import { FormEvent, ReactNode, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { getLegalDocuments, LegalDocumentListItem, registerUser, setAdminToken } from "../api/client";
import { PasswordInput } from "../components/PasswordInput";

const CODE_TO_ROUTE: Record<string, string> = {
  user_agreement: "/legal/user-agreement",
  privacy_policy: "/legal/privacy-policy",
  personal_data_consent: "/legal/personal-data-consent",
  public_data_consent: "/legal/public-data-consent",
  marketing_consent: "/legal/marketing-consent",
};

function LegalLink({
  children,
  to,
}: {
  children: ReactNode;
  to: string;
}) {
  return (
    <Link rel="noreferrer" target="_blank" to={to}>
      {children}
    </Link>
  );
}

export function RegisterPage() {
  const navigate = useNavigate();
  const errorRef = useRef<HTMLParagraphElement | null>(null);
  const [documents, setDocuments] = useState<LegalDocumentListItem[]>([]);
  const [displayName, setDisplayName] = useState("");
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [isAdultConfirmed, setIsAdultConfirmed] = useState(false);
  const [userAgreementAccepted, setUserAgreementAccepted] = useState(false);
  const [personalDataConsentAccepted, setPersonalDataConsentAccepted] = useState(false);
  const [marketingEmail, setMarketingEmail] = useState(false);
  const [marketingTelegram, setMarketingTelegram] = useState(false);
  const [marketingMax, setMarketingMax] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getLegalDocuments()
      .then(setDocuments)
      .catch((loadError) =>
        setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить документы."),
      );
  }, []);

  useEffect(() => {
    if (!error) {
      return;
    }

    errorRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
    errorRef.current?.focus();
  }, [error]);

  const docsByCode = useMemo(
    () => Object.fromEntries(documents.map((document) => [document.code, document])),
    [documents],
  );

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    const userAgreement = docsByCode.user_agreement;
    const personalDataConsent = docsByCode.personal_data_consent;
    const privacyPolicy = docsByCode.privacy_policy;
    const marketingConsent = docsByCode.marketing_consent;

    if (!userAgreement || !personalDataConsent || !privacyPolicy || !marketingConsent) {
      setError("Юридические документы ещё не загружены.");
      return;
    }

    try {
      const response = await registerUser({
        login,
        password,
        password_confirmation: passwordConfirmation,
        display_name: displayName,
        phone: phone.trim(),
        email: email || null,
        is_adult_confirmed: isAdultConfirmed,
        user_agreement: {
          accepted: userAgreementAccepted,
          version: userAgreement.version,
        },
        personal_data_consent: {
          accepted: personalDataConsentAccepted,
          version: personalDataConsent.version,
        },
        privacy_policy_version: privacyPolicy.version,
        marketing_consent: {
          version: marketingConsent.version,
          email: marketingEmail,
          telegram: marketingTelegram,
          max: marketingMax,
        },
      });
      setAdminToken(response.access_token);
      navigate("/account");
    } catch (registerError) {
      setError(registerError instanceof Error ? registerError.message : "Не удалось зарегистрироваться.");
    }
  }

  return (
    <section className="form-section">
      <h1>Регистрация</h1>
      <p className="muted">
        Обещаем по телефону беспокоить только по делу: если понадобится связаться насчёт обмена.
      </p>
      {error && (
        <p className="notice error" ref={errorRef} tabIndex={-1}>
          {error}
        </p>
      )}

      <form className="offer-form" onSubmit={submit}>
        <label>
          Имя в профиле *
          <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
          <span className="field-help">
            Это не логин и не публичное имя предмета. Имя в профиле видно вам и администраторам.
          </span>
        </label>
        <label>
          Логин *
          <input value={login} onChange={(event) => setLogin(event.target.value)} />
        </label>
        <label>
          Пароль *
          <PasswordInput
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        <label>
          Повторите пароль *
          <PasswordInput
            value={passwordConfirmation}
            onChange={(event) => setPasswordConfirmation(event.target.value)}
          />
        </label>
        <label>
          Телефон *
          <input
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
            required
          />
        </label>
        <label>
          Email
          <input value={email} onChange={(event) => setEmail(event.target.value)} />
        </label>

        <label className="checkbox-line">
          <input
            type="checkbox"
            checked={isAdultConfirmed}
            onChange={(event) => setIsAdultConfirmed(event.target.checked)}
          />
          Подтверждаю, что мне исполнилось 18 лет.
        </label>
        <label className="checkbox-line">
          <input
            type="checkbox"
            checked={userAgreementAccepted}
            onChange={(event) => setUserAgreementAccepted(event.target.checked)}
          />
          <span>
            Принимаю{" "}
            <LegalLink to={CODE_TO_ROUTE.user_agreement}>Пользовательское соглашение</LegalLink>.
          </span>
        </label>
        <label className="checkbox-line">
          <input
            type="checkbox"
            checked={personalDataConsentAccepted}
            onChange={(event) => setPersonalDataConsentAccepted(event.target.checked)}
          />
          <span>
            Даю согласие на обработку персональных данных и подтверждаю ознакомление с{" "}
            <LegalLink to={CODE_TO_ROUTE.personal_data_consent}>согласием</LegalLink> и{" "}
            <LegalLink to={CODE_TO_ROUTE.privacy_policy}>политикой обработки данных</LegalLink>.
          </span>
        </label>

        <fieldset className="plain-fieldset">
          <legend>Хочу получать новости проекта</legend>
          <label className="checkbox-line">
            <input
              type="checkbox"
              checked={marketingEmail}
              onChange={(event) => setMarketingEmail(event.target.checked)}
            />
            Email
          </label>
          <label className="checkbox-line">
            <input
              type="checkbox"
              checked={marketingTelegram}
              onChange={(event) => setMarketingTelegram(event.target.checked)}
            />
            Telegram
          </label>
          <label className="checkbox-line">
            <input
              type="checkbox"
              checked={marketingMax}
              onChange={(event) => setMarketingMax(event.target.checked)}
            />
            MAX
          </label>
          <LegalLink to={CODE_TO_ROUTE.marketing_consent}>Согласие на рассылки</LegalLink>
        </fieldset>

        <div className="actions">
          <button type="submit">Зарегистрироваться</button>
          <Link to="/login">Уже есть аккаунт</Link>
        </div>
      </form>
    </section>
  );
}
