import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  createTelegramLoginLink,
  getTelegramLoginStatus,
  loginUser,
  setAdminToken,
} from "../api/client";
import { PasswordInput } from "../components/PasswordInput";


export function UserLoginPage() {
  const navigate = useNavigate();
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [telegramPromptVisible, setTelegramPromptVisible] = useState(false);
  const [telegramLoginRequestId, setTelegramLoginRequestId] = useState<string | null>(null);
  const [telegramLoginUrl, setTelegramLoginUrl] = useState<string | null>(null);
  const [isTelegramLoginStarting, setIsTelegramLoginStarting] = useState(false);

  useEffect(() => {
    if (!telegramLoginRequestId) {
      return;
    }

    let isActive = true;
    const intervalId = window.setInterval(async () => {
      try {
        const status = await getTelegramLoginStatus(telegramLoginRequestId);

        if (!isActive) {
          return;
        }

        if (status.status === "authenticated" && status.access_token) {
          setAdminToken(status.access_token);
          setInfo("Telegram подтверждён. Выполняем вход...");
          window.clearInterval(intervalId);
          navigate("/account");
        }

        if (status.status === "expired") {
          setError("Ссылка Telegram-входа устарела. Создайте новую ссылку.");
          setTelegramLoginRequestId(null);
          setTelegramLoginUrl(null);
          window.clearInterval(intervalId);
        }
      } catch (pollError) {
        if (isActive) {
          setError(pollError instanceof Error ? pollError.message : "Не удалось проверить Telegram-вход.");
        }
      }
    }, 2000);

    return () => {
      isActive = false;
      window.clearInterval(intervalId);
    };
  }, [navigate, telegramLoginRequestId]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setInfo(null);

    try {
      const response = await loginUser(login, password);
      setAdminToken(response.access_token);
      navigate("/account");
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Не удалось войти.");
    }
  }

  function showAuthStub(provider: string) {
    setError(null);
    setInfo(
      `${provider}: вход и объединение аккаунтов будут подключены отдельным этапом через подтверждённый сценарий связывания.`,
    );
  }

  async function startTelegramLogin() {
    setError(null);
    setInfo(null);
    setIsTelegramLoginStarting(true);

    try {
      const loginLink = await createTelegramLoginLink();

      if (!loginLink.deep_link) {
        setError("Telegram-ссылка не создана. Проверьте TELEGRAM_BOT_USERNAME на backend.");
        return;
      }

      setTelegramLoginRequestId(loginLink.request_id);
      setTelegramLoginUrl(loginLink.deep_link);
      setTelegramPromptVisible(false);
      setInfo("Откройте Telegram, нажмите Start в боте и вернитесь на эту страницу.");
      window.open(loginLink.deep_link, "_blank", "noopener,noreferrer");
    } catch (telegramError) {
      setError(telegramError instanceof Error ? telegramError.message : "Не удалось начать Telegram-вход.");
    } finally {
      setIsTelegramLoginStarting(false);
    }
  }

  return (
    <section className="form-section">
      <h1>Вход</h1>
      {error && <p className="notice error">{error}</p>}
      {info && <p className="notice">{info}</p>}
      {telegramPromptVisible && (
        <div className="notice">
          <p>
            Если вы уже регистрировались на сайте с логином и паролем, сначала войдите по
            паролю, а затем подключите Telegram в личном кабинете. Так мы не создадим второй
            аккаунт и не потеряем ваши заявки.
          </p>
          <div className="actions">
            <button
              className="secondary-button"
              type="button"
              onClick={() => {
                setTelegramPromptVisible(false);
                setInfo("Введите логин и пароль, затем подключите Telegram в личном кабинете.");
              }}
            >
              У меня уже есть аккаунт сайта
            </button>
            <button
              type="button"
              onClick={startTelegramLogin}
              disabled={isTelegramLoginStarting}
            >
              Продолжить через Telegram
            </button>
          </div>
        </div>
      )}
      {telegramLoginUrl && (
        <p className="notice success">
          Telegram-ссылка создана. Если окно не открылось,{" "}
          <a href={telegramLoginUrl} target="_blank" rel="noreferrer">
            откройте бота вручную
          </a>
          . После подтверждения вход завершится автоматически.
        </p>
      )}
      <form className="offer-form" onSubmit={submit}>
        <label>
          Логин
          <input value={login} onChange={(event) => setLogin(event.target.value)} />
        </label>
        <label>
          Пароль
          <PasswordInput
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        <div className="actions">
          <button type="submit">Войти</button>
          <button
            className="secondary-button"
            type="button"
            onClick={() => showAuthStub("MAX")}
          >
            Войти через MAX / объединить аккаунты
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={() => {
              setError(null);
              setInfo(null);
              setTelegramPromptVisible(true);
            }}
          >
            Войти через Telegram / объединить аккаунты
          </button>
          <Link to="/register">Зарегистрироваться</Link>
          <Link to="/admin/login">Войти как администратор</Link>
        </div>
      </form>
    </section>
  );
}
