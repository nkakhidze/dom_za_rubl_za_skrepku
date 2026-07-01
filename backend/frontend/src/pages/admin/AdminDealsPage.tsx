import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { AdminDealListItem, getAdminDeals } from "../../api/client";

const DEAL_STATUSES = ["all", "new", "accepted", "rejected", "completed", "cancelled"];

export function AdminDealsPage() {
  const [deals, setDeals] = useState<AdminDealListItem[]>([]);
  const [statusFilter, setStatusFilter] = useState("all");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadDeals() {
    setIsLoading(true);
    setError(null);

    try {
      setDeals(await getAdminDeals());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить сделки.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadDeals();
  }, []);

  const filteredDeals = useMemo(
    () =>
      deals.filter((deal) => statusFilter === "all" || deal.deal_status === statusFilter),
    [deals, statusFilter],
  );

  return (
    <section>
      <div className="section-heading">
        <div>
          <h1>Админка сделок</h1>
          <p className="muted">Отклики пользователей на опубликованные офферы.</p>
        </div>
        <button type="button" onClick={() => void loadDeals()}>
          Обновить
        </button>
      </div>

      {error && <p className="notice error">{error}</p>}
      {isLoading && <p className="muted">Загружаем сделки...</p>}

      <div className="filters">
        <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          {DEAL_STATUSES.map((status) => (
            <option value={status} key={status}>
              {status === "all" ? "Все статусы" : status}
            </option>
          ))}
        </select>
      </div>

      {!isLoading && filteredDeals.length === 0 ? (
        <p className="notice">Сделок пока нет.</p>
      ) : (
        <div className="admin-list">
          {filteredDeals.map((deal) => (
            <article className="admin-row deal-row" key={deal.deal_id}>
              <div>
                <h2>{deal.offer_title || "Оффер без названия"}</h2>
                <p className="meta">
                  {deal.deal_id.slice(0, 8)} · {deal.deal_status_label || deal.deal_status} ·{" "}
                  {new Date(deal.deal_created_at).toLocaleDateString("ru-RU")}
                </p>
                <p className="meta">Предложено: {deal.item_title}</p>
                <p className="meta">
                  offer owner: {deal.offer_owner_display_name || deal.offer_owner_user_id || "-"} · item
                  owner: {deal.item_owner_display_name || deal.item_owner_user_id || "-"}
                </p>
              </div>
              <Link className="details-link" to={`/admin/deals/${deal.deal_id}`}>
                Открыть
              </Link>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
