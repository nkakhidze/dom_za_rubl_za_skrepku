import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getPublicOfferById, PublicOffer } from "../api/client";

export function OfferDetailPage() {
  const { offerId } = useParams();
  const [offer, setOffer] = useState<PublicOffer | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!offerId) {
      setError("Оффер не найден.");
      setIsLoading(false);
      return;
    }

    getPublicOfferById(offerId)
      .then(setOffer)
      .catch(() => setError("Не удалось загрузить оффер."))
      .finally(() => setIsLoading(false));
  }, [offerId]);

  if (isLoading) {
    return <p className="muted">Загружаем оффер...</p>;
  }

  if (error || !offer) {
    return (
      <section>
        <p className="notice error">{error || "Оффер не найден."}</p>
        <Link to="/">Вернуться в каталог</Link>
      </section>
    );
  }

  return (
    <article className="detail">
      <Link to="/">← Каталог</Link>
      <h1>{offer.title}</h1>
      <p className="meta">
        {offer.city || "Город не указан"} · {offer.offer_type}
        {offer.public_value !== null ? ` · ${offer.public_value} ₽` : ""}
      </p>

      {offer.photo_urls.length > 0 && (
        <div className="gallery">
          {offer.photo_urls.map((url) => (
            <img src={url} alt={offer.title} key={url} />
          ))}
        </div>
      )}

      <p className="description">{offer.description}</p>

      {offer.public_comment && (
        <section className="info-block">
          <h2>Комментарий</h2>
          <p>{offer.public_comment}</p>
        </section>
      )}

      {offer.participant_public_name && (
        <p className="meta">Участник: {offer.participant_public_name}</p>
      )}

      <p className="meta">
        Опубликовано: {new Date(offer.created_at).toLocaleDateString("ru-RU")}
      </p>
    </article>
  );
}
