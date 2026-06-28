import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  AdminOffer,
  AuthUser,
  clearAdminToken,
  getAdminOffers,
  getMe,
} from "../../api/client";

type Filter = "all" | "public" | "private";

export function AdminOffersPage() {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [offers, setOffers] = useState<AdminOffer[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [statusFilter, setStatusFilter] = useState("all");

  function logout() {
    clearAdminToken();
    setCurrentUser(null);
    setOffers([]);
    setError(null);
    navigate("/admin/login");
  }

  async function loadOffers() {
    setIsLoading(true);
    setError(null);

    try {
      setOffers(await getAdminOffers());
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Не удалось загрузить офферы.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    getMe()
      .then((user) => {
        setCurrentUser(user);
        void loadOffers();
      })
      .catch(() => {
        setCurrentUser(null);
        setError("Нужно войти в админку.");
      });
  }, []);

  const statuses = useMemo(
    () => Array.from(new Set(offers.map((offer) => offer.status))).sort(),
    [offers],
  );

  const filteredOffers = offers.filter((offer) => {
    if (filter === "public" && !offer.is_public) {
      return false;
    }

    if (filter === "private" && offer.is_public) {
      return false;
    }

    if (statusFilter !== "all" && offer.status !== statusFilter) {
      return false;
    }

    return true;
  });

  return (
    <section>
      <div className="section-heading">
        <div>
          <h1>Заявки пользователей</h1>
          <p className="muted">
            Входящие заявки пользователей. Заявка становится шагом цепочки только
            после принятия в обмен.
          </p>
        </div>
      </div>

      <div className="admin-token-panel">
        {currentUser ? (
          <p className="meta">
            Вы вошли как {currentUser.display_name || currentUser.login || currentUser.id} ·{" "}
            {currentUser.roles.join(", ")}
          </p>
        ) : (
          <p className="meta">Для доступа к админке войдите по login/password.</p>
        )}
        <div className="actions">
          <Link className="primary-link" to="/admin/login">
            Войти
          </Link>
          <button className="secondary-button" type="button" onClick={logout}>
            Выйти
          </button>
          <button className="secondary-button" type="button" onClick={loadOffers}>
            Обновить
          </button>
        </div>
      </div>

      {error && <p className="notice error">{error}</p>}
      {isLoading && <p className="muted">Загружаем офферы...</p>}

      <div className="filters">
        <select value={filter} onChange={(event) => setFilter(event.target.value as Filter)}>
          <option value="all">Все</option>
          <option value="public">Опубликованные</option>
          <option value="private">Неопубликованные</option>
        </select>
        <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          <option value="all">Все статусы</option>
          {statuses.map((status) => (
            <option value={status} key={status}>
              {status}
            </option>
          ))}
        </select>
      </div>

      {!isLoading && filteredOffers.length === 0 ? (
        <p className="notice">Заявок пока нет.</p>
      ) : (
        <div className="admin-list">
          {filteredOffers.map((offer) => (
            <article className="admin-row" key={offer.id}>
              <div className="admin-thumb">
                {offer.photo_urls[0] ? (
                  <img src={offer.photo_urls[0]} alt={offer.title} />
                ) : (
                  <span>Нет фото</span>
                )}
              </div>
              <div>
                <h2>{offer.title}</h2>
                <p className="meta">
                  заявка {offer.id.slice(0, 8)} · {offer.city || "город не указан"} ·{" "}
                  {offer.status_label || offer.status} · {offer.is_public ? "public" : "private"}
                </p>
                <p className="meta">
                  declared: {offer.declared_value ?? "-"} · moderated:{" "}
                  {offer.moderated_value ?? "-"} · public: {offer.public_value ?? "-"}
                </p>
                {offer.participant_public_name && (
                  <p className="meta">Участник: {offer.participant_public_name}</p>
                )}
              </div>
              <Link className="details-link" to={`/admin/offers/${offer.id}`}>
                Открыть
              </Link>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
