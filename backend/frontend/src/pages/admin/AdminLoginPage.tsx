import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { clearAdminToken, getMe, loginAdmin, setAdminToken, AuthUser } from "../../api/client";


export function AdminLoginPage() {
  const navigate = useNavigate();
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMe()
      .then(setCurrentUser)
      .catch(() => setCurrentUser(null));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    try {
      const response = await loginAdmin(login, password);
      setAdminToken(response.access_token);
      setCurrentUser(response.user);
      navigate("/admin/offers");
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Не удалось войти.");
    }
  }

  function logout() {
    clearAdminToken();
    setCurrentUser(null);
  }

  return (
    <section className="form-section">
      <div className="section-heading">
        <div>
          <h1>Вход в админку</h1>
          {currentUser && (
            <p className="muted">
              Вы вошли как {currentUser.display_name || currentUser.id} · {currentUser.roles.join(", ")}
            </p>
          )}
        </div>
      </div>

      {error && <p className="notice error">{error}</p>}

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
          <button className="secondary-button" type="button" onClick={logout}>
            Выйти
          </button>
          <Link to="/login">Войти как пользователь</Link>
          <Link to="/admin/offers">К заявкам</Link>
        </div>
      </form>
    </section>
  );
}
