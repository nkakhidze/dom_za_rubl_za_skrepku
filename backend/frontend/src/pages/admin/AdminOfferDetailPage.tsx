import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  AdminItem,
  AdminOffer,
  AdminOfferPhoto,
  getAdminItems,
  getAdminOfferById,
  getAdminOfferPhotos,
  selectOfferAsNext,
  updateOfferModeration,
  updateOfferStatus,
} from "../../api/client";

const OFFER_STATUSES = ["new", "reviewed", "hidden", "rejected"];
const STATUS_LABELS: Record<string, string> = {
  new: "Новая заявка",
  reviewed: "Просмотрена",
  selected: "Выбрана в цепочку",
  hidden: "Скрыта",
  rejected: "Отклонена",
};
const VISIBILITY_LABELS: Record<string, string> = {
  normal: "Обычная",
  low_priority: "Низкий приоритет",
  hidden: "Скрытая",
};
const EXCHANGE_PREFERENCE_LABELS: Record<string, string> = {
  any_offer: "Любой обмен",
  comparable_value_only: "Сопоставимая ценность",
};
const CONTRACT_STATUS_LABELS: Record<string, string> = {
  not_required: "Не требуется",
  required: "Требуется",
  prepared: "Подготовлен",
  signed: "Подписан",
};

function numberOrNull(value: string): number | null {
  if (!value.trim()) {
    return null;
  }

  return Number(value);
}

export function AdminOfferDetailPage() {
  const { offerId } = useParams();
  const [offer, setOffer] = useState<AdminOffer | null>(null);
  const [photos, setPhotos] = useState<AdminOfferPhoto[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [statusValue, setStatusValue] = useState("new");
  const [currentItem, setCurrentItem] = useState<AdminItem | null>(null);

  const [moderatedValue, setModeratedValue] = useState("");
  const [publicValue, setPublicValue] = useState("");
  const [valuationSource, setValuationSource] = useState("");
  const [moderationComment, setModerationComment] = useState("");
  const [publicComment, setPublicComment] = useState("");
  const [isPublic, setIsPublic] = useState(false);
  const [visibilityStatus, setVisibilityStatus] = useState<"normal" | "low_priority" | "hidden">(
    "normal",
  );
  const [sortPriority, setSortPriority] = useState("0");
  const [participantVisible, setParticipantVisible] = useState(false);
  const [participantPublicName, setParticipantPublicName] = useState("");
  const [dealPublicStory, setDealPublicStory] = useState("");
  const [dealVideoUrl, setDealVideoUrl] = useState("");
  const [dealOwnerName, setDealOwnerName] = useState("");
  const [dealIsPublic, setDealIsPublic] = useState(true);

  async function loadOffer() {
    if (!offerId) {
      setError("Оффер не найден.");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const [loadedOffer, loadedPhotos, currentItems] = await Promise.all([
        getAdminOfferById(offerId),
        getAdminOfferPhotos(offerId),
        getAdminItems({ is_current: true }),
      ]);
      setOffer(loadedOffer);
      setPhotos(loadedPhotos);
      setCurrentItem(currentItems[0] || null);
      setStatusValue(loadedOffer.status);
      setModeratedValue(loadedOffer.moderated_value?.toString() || "");
      setPublicValue(loadedOffer.public_value?.toString() || "");
      setValuationSource(loadedOffer.valuation_source || "");
      setModerationComment(loadedOffer.moderation_comment || "");
      setPublicComment(loadedOffer.public_comment || "");
      setIsPublic(loadedOffer.is_public);
      setVisibilityStatus(
        (loadedOffer.visibility_status || "normal") as "normal" | "low_priority" | "hidden",
      );
      setSortPriority(loadedOffer.sort_priority.toString());
      setParticipantVisible(loadedOffer.participant_visible);
      setParticipantPublicName(loadedOffer.participant_public_name || "");
      setDealPublicStory(loadedOffer.public_comment || "");
      setDealOwnerName(loadedOffer.participant_public_name || "");
    } catch (loadError) {
      setError(
        loadError instanceof Error ? loadError.message : "Не удалось загрузить оффер.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function submitAcceptIntoChain(event: FormEvent) {
    event.preventDefault();

    if (!offerId || !offer || !currentItem) {
      setError("Нужен текущий предмет цепочки и заявка.");
      return;
    }

    const confirmed = window.confirm(
      "Выбранная заявка станет новым предметом цепочки и появится в истории обменов. Продолжить?",
    );

    if (!confirmed) {
      return;
    }

    setError(null);
    setNotice(null);

    try {
      await selectOfferAsNext(offerId, {
        public_story: dealPublicStory || offer.public_comment || null,
        video_url: dealVideoUrl || null,
        photo_url: photos[0]?.photo_url || null,
        is_public: dealIsPublic,
      });
      setNotice("Заявка принята в цепочку. Новый предмет добавлен в историю обменов.");
      await loadOffer();
    } catch (saveError) {
      setError(
        saveError instanceof Error
          ? saveError.message
          : "Не удалось принять заявку в цепочку.",
      );
    }
  }

  useEffect(() => {
    void loadOffer();
  }, [offerId]);

  async function submitModeration(event: FormEvent) {
    event.preventDefault();

    if (!offerId) {
      return;
    }

    setError(null);
    setNotice(null);

    try {
      const updated = await updateOfferModeration(offerId, {
        moderated_value: numberOrNull(moderatedValue),
        visibility_status: visibilityStatus,
      });
      setOffer(updated);
      setStatusValue(updated.status);
      setIsPublic(updated.is_public);
      setNotice("Модерация сохранена.");
    } catch (saveError) {
      setError(
        saveError instanceof Error ? saveError.message : "Не удалось сохранить модерацию.",
      );
    }
  }

  async function submitStatus(event: FormEvent) {
    event.preventDefault();

    if (!offerId) {
      return;
    }

    setError(null);
    setNotice(null);

    try {
      const updated = await updateOfferStatus(offerId, statusValue);
      setOffer(updated);
      setStatusValue(updated.status);
      setIsPublic(updated.is_public);
      setNotice("Статус сохранён.");
    } catch (saveError) {
      setError(
        saveError instanceof Error ? saveError.message : "Не удалось сохранить статус.",
      );
    }
  }

  if (isLoading) {
    return <p className="muted">Загружаем оффер...</p>;
  }

  if (!offer) {
    return (
      <section>
        <p className="notice error">{error || "Оффер не найден."}</p>
        <Link to="/admin/offers">Вернуться к списку</Link>
      </section>
    );
  }

  return (
    <section className="admin-detail">
      <Link to="/admin/offers">← Все офферы</Link>
      <div className="section-heading">
        <div>
          <h1>{offer.title}</h1>
          <p className="meta">
            {offer.id} · {offer.city || "город не указан"} · {offer.offer_type}
          </p>
        </div>
      </div>

      {error && <p className="notice error">{error}</p>}
      {notice && <p className="notice success">{notice}</p>}

      <div className="admin-layout">
        <div>
          <section className="admin-panel">
            <h2>Данные заявки</h2>
            <p>{offer.description}</p>
            <dl className="field-list">
              <div>
                <dt>Цена пользователя</dt>
                <dd>{offer.declared_value ?? "-"}</dd>
              </div>
              <div>
                <dt>Предпочтения по обмену</dt>
                <dd>
                  {EXCHANGE_PREFERENCE_LABELS[offer.exchange_preference] || offer.exchange_preference}
                </dd>
              </div>
              <div>
                <dt>Статус</dt>
                <dd>{offer.status_label || STATUS_LABELS[offer.status] || offer.status}</dd>
              </div>
              <div>
                <dt>Видимость</dt>
                <dd>{VISIBILITY_LABELS[offer.visibility_status] || offer.visibility_status}</dd>
              </div>
              <div>
                <dt>Имя пользователя</dt>
                <dd>{offer.participant_public_name || "-"}</dd>
              </div>
              <div>
                <dt>Согласие</dt>
                <dd>{offer.consent_accepted ? "Принято" : "Не принято"}</dd>
              </div>
              <div>
                <dt>Статус договора</dt>
                <dd>
                  {offer.contract_status
                    ? CONTRACT_STATUS_LABELS[offer.contract_status] || offer.contract_status
                    : "-"}
                </dd>
              </div>
            </dl>
          </section>

          <section className="admin-panel">
            <h2>Принять в цепочку обменов</h2>
            {currentItem ? (
              <>
                <p className="meta">
                  Отдадим текущий предмет: <strong>{currentItem.title}</strong>
                </p>
                <p className="meta">
                  Получим предмет из заявки: <strong>{offer.title}</strong>
                </p>
                <form className="offer-form" onSubmit={submitAcceptIntoChain}>
                  <label>
                    Публикуемое имя пользователя
                    <input
                      value={dealOwnerName}
                      onChange={(event) => setDealOwnerName(event.target.value)}
                      disabled
                    />
                  </label>
                  <label>
                    Публикуемая история предмета
                    <textarea
                      value={dealPublicStory}
                      onChange={(event) => setDealPublicStory(event.target.value)}
                      rows={3}
                    />
                  </label>
                  <label>
                    video_url
                    <input
                      value={dealVideoUrl}
                      onChange={(event) => setDealVideoUrl(event.target.value)}
                    />
                  </label>
                  <label className="checkbox">
                    <input
                      checked={dealIsPublic}
                      onChange={(event) => setDealIsPublic(event.target.checked)}
                      type="checkbox"
                    />
                    Опубликовать переход в истории обменов
                  </label>
                  <button type="submit">Принять заявку в цепочку</button>
                </form>
              </>
            ) : (
              <p className="notice">
                Сначала создайте текущий предмет цепочки на странице “Предметы”.
              </p>
            )}
          </section>

          <section className="admin-panel">
            <h2>Фото</h2>
            {photos.length === 0 ? (
              <p className="muted">Фото нет.</p>
            ) : (
              <div className="gallery">
                {photos.map((photo) => (
                  <img src={photo.photo_url} alt={offer.title} key={photo.id} />
                ))}
              </div>
            )}
          </section>
        </div>

        <div>
          <form className="admin-panel offer-form" onSubmit={submitModeration}>
            <h2>Модерация</h2>
            <label>
              Цена админа
              <input
                inputMode="numeric"
                value={moderatedValue}
                onChange={(event) => setModeratedValue(event.target.value)}
              />
            </label>
            <label>
              Видимость
              <select
                value={visibilityStatus}
                onChange={(event) =>
                  setVisibilityStatus(event.target.value as "normal" | "low_priority" | "hidden")
                }
              >
                <option value="normal">Обычная</option>
                <option value="low_priority">Низкий приоритет</option>
                <option value="hidden">Скрытая</option>
              </select>
            </label>
            <button type="submit">Сохранить модерацию</button>
          </form>

          <form className="admin-panel offer-form" onSubmit={submitStatus}>
            <h2>Статус</h2>
            <label>
              Статус
              <select
                value={statusValue}
                onChange={(event) => setStatusValue(event.target.value)}
              >
                {statusValue === "selected" && (
                  <option value="selected" disabled>
                    Выбрана в цепочку
                  </option>
                )}
                {OFFER_STATUSES.map((status) => (
                  <option value={status} key={status}>
                    {STATUS_LABELS[status]}
                  </option>
                ))}
              </select>
            </label>
            <button type="submit">Сохранить статус</button>
          </form>
        </div>
      </div>
    </section>
  );
}
