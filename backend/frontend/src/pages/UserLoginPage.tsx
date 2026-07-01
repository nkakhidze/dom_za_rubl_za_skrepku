import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { loginUser, setAdminToken } from "../api/client";


export function UserLoginPage() {
  const navigate = useNavigate();
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

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

  return (
    <section className="form-section">
      <h1>Вход</h1>
      {error && <p className="notice error">{error}</p>}
      {info && <p className="notice">{info}</p>}
      <form className="offer-form" onSubmit={submit}>
        <label>
          Логин
          <input value={login} onChange={(event) => setLogin(event.target.value)} />
        </label>
        <label>
          Пароль
          <input
            type="password"
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
            onClick={() => showAuthStub("Telegram")}
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
