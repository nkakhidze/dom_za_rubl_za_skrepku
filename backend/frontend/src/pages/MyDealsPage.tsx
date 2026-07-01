import { useEffect, useState } from "react";

import { getMyDeals, UserDeal } from "../api/client";


export function MyDealsPage() {
  const [deals, setDeals] = useState<UserDeal[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getMyDeals()
      .then(setDeals)
      .catch((loadError) => {
        setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить сделки.");
      })
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <section className="form-section">
      <div className="section-heading">
        <div>
          <h1>Мои сделки</h1>
          <p className="muted">Сделки, где вы владелец заявки или предложенного предмета.</p>
        </div>
      </div>

      {error && <p className="notice error">{error}</p>}
      {isLoading && <p>Загрузка...</p>}
      {!isLoading && deals.length === 0 && <p className="notice">Сделок пока нет.</p>}

      <div className="simple-list">
        {deals.map((deal) => (
          <article className="notice" key={deal.id}>
            <h2>{deal.offer_title || "Оффер без названия"}</h2>
            <p>Предложено: {deal.item_title}</p>
            <p className="meta">
              {deal.status_label || deal.status} ·{" "}
              {new Date(deal.created_at).toLocaleDateString("ru-RU")}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
