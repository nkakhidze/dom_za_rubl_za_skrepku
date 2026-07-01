import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  AccountResponse,
  TelegramLinkStatus,
  clearAdminToken,
  createTelegramLink,
  getAccount,
  getTelegramLinkStatus,
  updateAccount,
} from "../api/client";

export function AccountPage() {
  const navigate = useNavigate();
  const [account, setAccount] = useState<AccountResponse | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [telegramStatus, setTelegramStatus] = useState<TelegramLinkStatus | null>(null);
  const [isLinkingTelegram, setIsLinkingTelegram] = useState(false);

  useEffect(() => {
    getAccount()
      .then((loadedAccount) => {
        setAccount(loadedAccount);
        setDisplayName(loadedAccount.display_name || "");
        setPhone(loadedAccount.phone || "");
        setEmail(loadedAccount.email || "");
      })
      .catch((loadError) => {
        setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить кабинет.");
      });
  }, []);

  useEffect(() => {
    if (!account) {
      return;
    }

    refreshTelegramStatus();
  }, [account]);

  async function refreshTelegramStatus() {
    try {
      setTelegramStatus(await getTelegramLinkStatus());
    } catch {
      setTelegramStatus(null);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    setNotice(null);

    try {
      const updated = await updateAccount({
        display_name: displayName,
        phone: phone || null,
        email: email || null,
      });
      setAccount(updated);
      setDisplayName(updated.display_name || "");
      setPhone(updated.phone || "");
      setEmail(updated.email || "");
      setIsEditing(false);
      setNotice("Профиль сохранён.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Не удалось сохранить профиль.");
    } finally {
      setIsSaving(false);
    }
  }

  function logout() {
    clearAdminToken();
    navigate("/login");
  }

  function showMessengerStub(platformName: string) {
    setError(null);
    setNotice(
      `${platformName} будет подключён отдельным безопасным сценарием подтверждения и объединения аккаунтов.`,
    );
  }

  function isExternalTelegramLink(value: string) {
    try {
      const url = new URL(value);
      return url.protocol === "https:" || url.protocol === "tg:";
    } catch {
      return false;
    }
  }

  async function linkTelegram() {
    setIsLinkingTelegram(true);
    setError(null);
    setNotice(null);

    try {
      const link = await createTelegramLink();
      setTelegramStatus(link);

      if (link.telegram_connected) {
        setNotice("Telegram уже подключён.");
      } else if (link.deep_link) {
        if (isExternalTelegramLink(link.deep_link)) {
          setNotice("Ссылка для привязки Telegram создана. Откройте её и нажмите Start в боте.");
          window.open(link.deep_link, "_blank", "noopener,noreferrer");
        } else {
          setError(
            "Backend создал токен привязки, но не смог собрать Telegram-ссылку. Укажите TELEGRAM_BOT_USERNAME в .env и перезапустите backend.",
          );
        }
      } else {
        setError(
          "Backend создал токен привязки, но не вернул Telegram-ссылку. Укажите TELEGRAM_BOT_USERNAME в .env и перезапустите backend.",
        );
      }
    } catch (linkError) {
      setError(linkError instanceof Error ? linkError.message : "Не удалось создать ссылку Telegram.");
    } finally {
      setIsLinkingTelegram(false);
    }
  }

  if (error && !account) {
    return (
      <section className="form-section">
        <p className="notice error">{error}</p>
        <Link to="/login">Войти</Link>
      </section>
    );
  }

  if (!account) {
    return <p>Загрузка личного кабинета...</p>;
  }

  return (
    <section className="form-section">
      <div className="section-heading">
        <div>
          <h1>Личный кабинет</h1>
          <p className="muted">Профиль зарегистрированного пользователя.</p>
        </div>
        <button className="secondary-button" type="button" onClick={logout}>
          Выйти
        </button>
      </div>

      {error && <p className="notice error">{error}</p>}
      {notice && <p className="notice success">{notice}</p>}

      <section className="card">
        <div className="section-heading compact-heading">
          <h2>Профиль</h2>
          {!isEditing && (
            <button className="secondary-button" type="button" onClick={() => setIsEditing(true)}>
              Редактировать
            </button>
          )}
        </div>

        {isEditing ? (
          <form className="offer-form" onSubmit={submit}>
            <label>
              Как к вам обращаться?
              <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
            </label>
            <label>
              Телефон
              <input value={phone} onChange={(event) => setPhone(event.target.value)} />
            </label>
            <label>
              Email
              <input value={email} onChange={(event) => setEmail(event.target.value)} />
            </label>
            <div className="actions">
              <button type="submit" disabled={isSaving}>
                Сохранить
              </button>
              <button
                className="secondary-button"
                type="button"
                onClick={() => {
                  setDisplayName(account.display_name || "");
                  setPhone(account.phone || "");
                  setEmail(account.email || "");
                  setIsEditing(false);
                }}
              >
                Отмена
              </button>
            </div>
          </form>
        ) : (
          <dl className="field-list">
            <div>
              <dt>Имя</dt>
              <dd>{account.display_name || "-"}</dd>
            </div>
            <div>
              <dt>Логин</dt>
              <dd>{account.login || "-"}</dd>
            </div>
            <div>
              <dt>Телефон</dt>
              <dd>
                {account.phone || "-"} {account.phone_verified ? "подтверждён" : ""}
              </dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{account.email || "-"}</dd>
            </div>
            <div>
              <dt>Дата регистрации</dt>
              <dd>{new Date(account.created_at).toLocaleString("ru-RU")}</dd>
            </div>
          </dl>
        )}
      </section>

      <section className="card">
        <h2>Связанные аккаунты</h2>
        <p className="muted">
          {telegramStatus?.telegram_connected
            ? `Telegram подключён${telegramStatus.telegram_username ? `: @${telegramStatus.telegram_username}` : ""}`
            : "Telegram не подключён"}
        </p>
        <div className="actions">
          <button
            className="secondary-button"
            type="button"
            onClick={() => showMessengerStub("MAX")}
          >
            Войти через MAX / объединить аккаунты
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={linkTelegram}
            disabled={isLinkingTelegram || telegramStatus?.telegram_connected}
          >
            {telegramStatus?.telegram_connected
              ? "Telegram подключён"
              : "Войти через Telegram / объединить аккаунты"}
          </button>
          <button className="secondary-button" type="button" onClick={refreshTelegramStatus}>
            Проверить подключение
          </button>
        </div>
      </section>
    </section>
  );
}
