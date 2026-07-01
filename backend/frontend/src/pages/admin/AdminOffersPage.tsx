import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  AdminOffer,
  AuthUser,
  clearAdminToken,
  getAdminOffersFiltered,
  getMe,
} from "../../api/client";

const OFFER_STATUS_OPTIONS = ["all", "new", "reviewed", "selected", "hidden", "rejected"];
const STATUS_LABELS: Record<string, string> = {
  all: "Все рабочие статусы",
  new: "Новая заявка",
  reviewed: "Просмотрена",
  selected: "Выбрана в цепочку",
  hidden: "Скрыта",
  rejected: "Отклонена",
};
const VISIBILITY_OPTIONS = ["normal", "low_priority", "hidden"];
const VISIBILITY_LABELS: Record<string, string> = {
  normal: "Обычная",
  low_priority: "Низкий приоритет",
  hidden: "Скрытая",
};
const SORT_OPTIONS = [
  ["value_desc", "По стоимости"],
  ["created_at_desc", "По дате"],
  ["priority", "По приоритету"],
] as const;

export function AdminOffersPage() {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [offers, setOffers] = useState<AdminOffer[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [visibilityFilters, setVisibilityFilters] = useState<string[]>(VISIBILITY_OPTIONS);
  const [sortMode, setSortMode] = useState("value_desc");

  const visibleVisibilityFilters =
    visibilityFilters.length === 0 || visibilityFilters.length === VISIBILITY_OPTIONS.length
      ? undefined
      : visibilityFilters;

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
      setOffers(
        await getAdminOffersFiltered({
          offer_status: statusFilter,
          visibility_status: visibleVisibilityFilters,
          sort: sortMode,
        }),
      );
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

  useEffect(() => {
    if (currentUser) {
      void loadOffers();
    }
  }, [statusFilter, visibilityFilters, sortMode]);

  function toggleVisibilityFilter(visibility: string) {
    setVisibilityFilters((current) =>
      current.includes(visibility)
        ? current.filter((item) => item !== visibility)
        : [...current, visibility],
    );
  }

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
        <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          <option value="all">Все статусы</option>
          {OFFER_STATUS_OPTIONS.filter((status) => status !== "all").map((status) => (
            <option value={status} key={status}>
              {STATUS_LABELS[status]}
            </option>
          ))}
        </select>
        <details className="filter-dropdown">
          <summary>
            Видимость:{" "}
            {visibilityFilters.length === VISIBILITY_OPTIONS.length || visibilityFilters.length === 0
              ? "все"
              : visibilityFilters.map((item) => VISIBILITY_LABELS[item]).join(", ")}
          </summary>
          <div className="filter-dropdown-menu">
            {VISIBILITY_OPTIONS.map((visibility) => (
              <label className="checkbox" key={visibility}>
                <input
                  checked={visibilityFilters.includes(visibility)}
                  onChange={() => toggleVisibilityFilter(visibility)}
                  type="checkbox"
                />
                {VISIBILITY_LABELS[visibility]}
              </label>
            ))}
          </div>
        </details>
        <select value={sortMode} onChange={(event) => setSortMode(event.target.value)}>
          {SORT_OPTIONS.map(([value, label]) => (
            <option value={value} key={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {!isLoading && offers.length === 0 ? (
        <p className="notice">Заявок пока нет.</p>
      ) : (
        <div className="admin-list">
          {offers.map((offer) => (
            <article className="admin-row" key={offer.id}>
              <div className="admin-thumb">
                {(offer.thumbnail_urls[0] || offer.photo_urls[0]) ? (
                  <img src={offer.thumbnail_urls[0] || offer.photo_urls[0]} alt={offer.title} />
                ) : (
                  <span>Нет фото</span>
                )}
              </div>
              <div>
                <h2>{offer.title}</h2>
                <p className="meta">
                  заявка {offer.id.slice(0, 8)} · {offer.city || "город не указан"} ·{" "}
                  {offer.status_label || STATUS_LABELS[offer.status] || offer.status} · видимость:{" "}
                  {VISIBILITY_LABELS[offer.visibility_status] || offer.visibility_status}
                </p>
                <p className="meta">
                  оценка пользователя: {offer.declared_value ?? "-"} · оценка админа:{" "}
                  {offer.moderated_value ?? "-"} · приоритет: {offer.sort_priority}
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
