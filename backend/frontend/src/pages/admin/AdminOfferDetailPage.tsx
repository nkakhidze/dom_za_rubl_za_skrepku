import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  AdminOffer,
  AdminOfferPhoto,
  getAdminOfferById,
  getAdminOfferPhotos,
  updateOfferModeration,
  updateOfferStatus,
} from "../../api/client";

const OFFER_STATUSES = [
  "new",
  "need_details",
  "shortlisted",
  "rejected",
  "accepted",
  "completed",
  "cancelled",
];

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

  const [moderatedValue, setModeratedValue] = useState("");
  const [publicValue, setPublicValue] = useState("");
  const [valuationSource, setValuationSource] = useState("");
  const [moderationComment, setModerationComment] = useState("");
  const [publicComment, setPublicComment] = useState("");
  const [isPublic, setIsPublic] = useState(false);
  const [participantVisible, setParticipantVisible] = useState(false);
  const [participantPublicName, setParticipantPublicName] = useState("");

  async function loadOffer() {
    if (!offerId) {
      setError("Оффер не найден.");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const [loadedOffer, loadedPhotos] = await Promise.all([
        getAdminOfferById(offerId),
        getAdminOfferPhotos(offerId),
      ]);
      setOffer(loadedOffer);
      setPhotos(loadedPhotos);
      setStatusValue(loadedOffer.status);
      setModeratedValue(loadedOffer.moderated_value?.toString() || "");
      setPublicValue(loadedOffer.public_value?.toString() || "");
      setValuationSource(loadedOffer.valuation_source || "");
      setModerationComment(loadedOffer.moderation_comment || "");
      setPublicComment(loadedOffer.public_comment || "");
      setIsPublic(loadedOffer.is_public);
      setParticipantVisible(loadedOffer.participant_visible);
      setParticipantPublicName(loadedOffer.participant_public_name || "");
    } catch (loadError) {
      setError(
        loadError instanceof Error ? loadError.message : "Не удалось загрузить оффер.",
      );
    } finally {
      setIsLoading(false);
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
        public_value: numberOrNull(publicValue),
        valuation_source: valuationSource || null,
        moderation_comment: moderationComment || null,
        public_comment: publicComment || null,
        is_public: isPublic,
        participant_visible: participantVisible,
        participant_public_name: participantPublicName || null,
      });
      setOffer(updated);
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
            <h2>Данные оффера</h2>
            <p>{offer.description}</p>
            <dl className="field-list">
              <div>
                <dt>declared_value</dt>
                <dd>{offer.declared_value ?? "-"}</dd>
              </div>
              <div>
                <dt>exchange_preference</dt>
                <dd>{offer.exchange_preference}</dd>
              </div>
              <div>
                <dt>status</dt>
                <dd>{offer.status}</dd>
              </div>
              <div>
                <dt>is_public</dt>
                <dd>{offer.is_public ? "true" : "false"}</dd>
              </div>
              <div>
                <dt>participant</dt>
                <dd>{offer.participant_public_name || "-"}</dd>
              </div>
              <div>
                <dt>consent</dt>
                <dd>{offer.consent_accepted ? "accepted" : "not accepted"}</dd>
              </div>
              <div>
                <dt>contract_status</dt>
                <dd>{offer.contract_status || "-"}</dd>
              </div>
            </dl>
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
              moderated_value
              <input
                inputMode="numeric"
                value={moderatedValue}
                onChange={(event) => setModeratedValue(event.target.value)}
              />
            </label>
            <label>
              public_value
              <input
                inputMode="numeric"
                value={publicValue}
                onChange={(event) => setPublicValue(event.target.value)}
              />
            </label>
            <label>
              valuation_source
              <textarea
                value={valuationSource}
                onChange={(event) => setValuationSource(event.target.value)}
                rows={3}
              />
            </label>
            <label>
              moderation_comment
              <textarea
                value={moderationComment}
                onChange={(event) => setModerationComment(event.target.value)}
                rows={3}
              />
            </label>
            <label>
              public_comment
              <textarea
                value={publicComment}
                onChange={(event) => setPublicComment(event.target.value)}
                rows={3}
              />
            </label>
            <label>
              participant_public_name
              <input
                value={participantPublicName}
                onChange={(event) => setParticipantPublicName(event.target.value)}
              />
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={participantVisible}
                onChange={(event) => setParticipantVisible(event.target.checked)}
              />
              participant_visible
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(event) => setIsPublic(event.target.checked)}
              />
              is_public
            </label>
            <button type="submit">Сохранить модерацию</button>
          </form>

          <form className="admin-panel offer-form" onSubmit={submitStatus}>
            <h2>Статус</h2>
            <label>
              status
              <select
                value={statusValue}
                onChange={(event) => setStatusValue(event.target.value)}
              >
                {OFFER_STATUSES.map((status) => (
                  <option value={status} key={status}>
                    {status}
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
