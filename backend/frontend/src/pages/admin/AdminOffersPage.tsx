import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  AdminOffer,
  clearAdminToken,
  getAdminOffers,
  getAdminToken,
  setAdminToken,
} from "../../api/client";

type Filter = "all" | "public" | "private";

export function AdminOffersPage() {
  const [tokenInput, setTokenInput] = useState(getAdminToken());
  const [offers, setOffers] = useState<AdminOffer[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [statusFilter, setStatusFilter] = useState("all");

  function saveToken() {
    setAdminToken(tokenInput.trim());
    void loadOffers();
  }

  function resetToken() {
    clearAdminToken();
    setTokenInput("");
    setOffers([]);
    setError(null);
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
    if (getAdminToken()) {
      void loadOffers();
    }
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
          <h1>Админка офферов</h1>
          <p className="muted">Модерация, публикация и смена статуса.</p>
        </div>
      </div>

      <div className="admin-token-panel">
        <label>
          Admin token
          <input
            type="password"
            value={tokenInput}
            onChange={(event) => setTokenInput(event.target.value)}
            placeholder="Authorization Bearer token"
          />
        </label>
        <div className="actions">
          <button type="button" onClick={saveToken}>
            Сохранить токен
          </button>
          <button className="secondary-button" type="button" onClick={resetToken}>
            Сбросить токен
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
        <p className="notice">Офферов пока нет.</p>
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
                  {offer.id.slice(0, 8)} · {offer.city || "город не указан"} ·{" "}
                  {offer.status} · {offer.is_public ? "public" : "private"}
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
