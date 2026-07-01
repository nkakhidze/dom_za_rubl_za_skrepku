import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getMyOffers, UserOffer } from "../api/client";


function formatValue(value: number | null) {
  return value === null || value === undefined ? "не указана" : `${value.toLocaleString("ru-RU")} ₽`;
}


export function MyItemsPage() {
  const [offers, setOffers] = useState<UserOffer[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getMyOffers()
      .then(setOffers)
      .catch((loadError) => {
        setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить ваши предложения.");
      })
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <section className="form-section">
      <div className="section-heading">
        <div>
          <h1>Мои предложения</h1>
          <p className="muted">Предметы и услуги, которые вы предложили проекту.</p>
        </div>
        <Link className="primary-link" to="/new-offer">
          Предложить обмен
        </Link>
      </div>

      {error && <p className="notice error">{error}</p>}
      {isLoading && <p>Загрузка...</p>}
      {!isLoading && offers.length === 0 && (
        <p className="notice">Вы пока не подавали предложения.</p>
      )}

      <div className="simple-list">
        {offers.map((offer) => (
          <article className="notice item-row" key={offer.id}>
            <div className="admin-thumb">
              {(offer.thumbnail_urls[0] || offer.photo_urls[0]) ? (
                <img src={offer.thumbnail_urls[0] || offer.photo_urls[0]} alt="" />
              ) : (
                "Нет фото"
              )}
            </div>
            <div>
              <h2>{offer.title}</h2>
              <p>{offer.description}</p>
              <p className="meta">
                {offer.city || "город не указан"} · {offer.status_label || offer.status} · оценка:{" "}
                {formatValue(offer.declared_value)}
              </p>
              {offer.public_comment && <p>{offer.public_comment}</p>}
              <p className="meta">
                Подано {new Date(offer.created_at).toLocaleDateString("ru-RU")}
              </p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
