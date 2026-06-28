import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  createDeal,
  getPublicOfferById,
  getUserItems,
  PublicOffer,
  UserItem,
} from "../api/client";

export function OfferDetailPage() {
  const { offerId } = useParams();
  const [offer, setOffer] = useState<PublicOffer | null>(null);
  const [items, setItems] = useState<UserItem[]>([]);
  const [userId, setUserId] = useState("");
  const [selectedItemId, setSelectedItemId] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmittingDeal, setIsSubmittingDeal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dealError, setDealError] = useState<string | null>(null);
  const [dealNotice, setDealNotice] = useState<string | null>(null);

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

  async function loadItems() {
    if (!userId.trim()) {
      setDealError("Укажите user_id.");
      return;
    }

    setDealError(null);
    setDealNotice(null);

    try {
      const loadedItems = await getUserItems(userId.trim());
      setItems(loadedItems);
      setSelectedItemId(loadedItems[0]?.id || "");
    } catch (loadError) {
      setItems([]);
      setSelectedItemId("");
      setDealError(loadError instanceof Error ? loadError.message : "Не удалось загрузить items.");
    }
  }

  async function submitDeal(event: FormEvent) {
    event.preventDefault();

    if (!offerId || !selectedItemId) {
      setDealError("Выберите предмет для обмена.");
      return;
    }

    setIsSubmittingDeal(true);
    setDealError(null);
    setDealNotice(null);

    try {
      await createDeal({
        offer_id: offerId,
        item_id: selectedItemId,
      });
      setDealNotice("Отклик отправлен.");
    } catch (createError) {
      setDealError(createError instanceof Error ? createError.message : "Не удалось отправить отклик.");
    } finally {
      setIsSubmittingDeal(false);
    }
  }

  if (isLoading) {
    return <p className="muted">Загружаем оффер...</p>;
  }

  if (error || !offer) {
    return (
      <section>
        <p className="notice error">{error || "Оффер не найден."}</p>
        <Link to="/">Вернуться к истории обменов</Link>
      </section>
    );
  }

  return (
    <article className="detail">
      <Link to="/">← История обменов</Link>
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

      <section className="admin-panel offer-form response-panel">
        <h2>Предложить обмен</h2>
        {dealError && <p className="notice error">{dealError}</p>}
        {dealNotice && <p className="notice success">{dealNotice}</p>}
        <label>
          user_id
          <input value={userId} onChange={(event) => setUserId(event.target.value)} />
        </label>
        <div className="actions">
          <button className="secondary-button" type="button" onClick={() => void loadItems()}>
            Загрузить мои items
          </button>
          <Link className="primary-link" to="/my/items">
            Создать item
          </Link>
        </div>

        {items.length === 0 ? (
          <p className="muted">Загрузите items или создайте предмет для обмена.</p>
        ) : (
          <form className="offer-form" onSubmit={submitDeal}>
            <label>
              Предмет для обмена
              <select
                value={selectedItemId}
                onChange={(event) => setSelectedItemId(event.target.value)}
              >
                {items.map((item) => (
                  <option value={item.id} key={item.id}>
                    {item.title} · {item.status}
                  </option>
                ))}
              </select>
            </label>
            <button type="submit" disabled={isSubmittingDeal || !selectedItemId}>
              Предложить обмен
            </button>
          </form>
        )}
      </section>

      <p className="meta">
        Опубликовано: {new Date(offer.created_at).toLocaleDateString("ru-RU")}
      </p>
    </article>
  );
}
