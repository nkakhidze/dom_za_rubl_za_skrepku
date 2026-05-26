import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getPublicOffers, PublicOffer } from "../api/client";

export function OffersPage() {
  const [offers, setOffers] = useState<PublicOffer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPublicOffers()
      .then(setOffers)
      .catch(() => setError("Не удалось загрузить каталог. Попробуйте позже."))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return <p className="muted">Загружаем каталог...</p>;
  }

  if (error) {
    return <p className="notice error">{error}</p>;
  }

  return (
    <section>
      <div className="section-heading">
        <div>
          <h1>Публичный каталог</h1>
          <p className="muted">Опубликованные предложения для цепочки обменов.</p>
        </div>
        <Link className="primary-link" to="/new-offer">
          Подать оффер
        </Link>
      </div>

      {offers.length === 0 ? (
        <p className="notice">Пока нет опубликованных офферов.</p>
      ) : (
        <div className="offer-grid">
          {offers.map((offer) => (
            <article className="offer-card" key={offer.id}>
              <div className="thumb">
                {offer.photo_urls[0] ? (
                  <img src={offer.photo_urls[0]} alt={offer.title} />
                ) : (
                  <span>Нет фото</span>
                )}
              </div>
              <div className="offer-card-body">
                <h2>{offer.title}</h2>
                <p className="meta">
                  {offer.city || "Город не указан"}
                  {offer.public_value !== null ? ` · ${offer.public_value} ₽` : ""}
                </p>
                <p>{offer.description.slice(0, 140)}</p>
                {offer.participant_public_name && (
                  <p className="meta">Участник: {offer.participant_public_name}</p>
                )}
                <Link className="details-link" to={`/offers/${offer.id}`}>
                  Подробнее
                </Link>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
