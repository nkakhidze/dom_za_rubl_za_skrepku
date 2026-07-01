import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { createOffer, getAdminToken, getMe, uploadImage } from "../api/client";
import { getWebExternalUserId } from "../utils/webUser";

type SubmitState = "idle" | "submitting" | "success" | "error";

const MAX_DECLARED_VALUE = 400000;

function parseDeclaredValue(rawValue: string): number | null {
  const normalized = rawValue.trim().replace(/\s+/g, "");

  if (!normalized) {
    return null;
  }

  if (!/^\d+$/.test(normalized)) {
    return Number.NaN;
  }

  if (normalized.length > MAX_DECLARED_VALUE.toString().length) {
    return MAX_DECLARED_VALUE;
  }

  return Math.min(Number(normalized), MAX_DECLARED_VALUE);
}

export function NewOfferPage() {
  const externalUserId = useMemo(() => getWebExternalUserId(), []);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [offerType, setOfferType] = useState<"physical_item" | "service">("physical_item");
  const [city, setCity] = useState("");
  const [declaredValue, setDeclaredValue] = useState("");
  const [exchangePreference, setExchangePreference] = useState<
    "any_offer" | "comparable_value_only"
  >("any_offer");
  const [participantPublicName, setParticipantPublicName] = useState("");
  const [participantVisible, setParticipantVisible] = useState(true);
  const [files, setFiles] = useState<File[]>([]);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const [createdOfferId, setCreatedOfferId] = useState<string | null>(null);

  useEffect(() => {
    if (!getAdminToken()) {
      setIsAuthenticated(false);
      setAuthChecked(true);
      return;
    }

    getMe()
      .then(() => setIsAuthenticated(true))
      .catch(() => setIsAuthenticated(false))
      .finally(() => setAuthChecked(true));
  }, []);

  function handleFiles(nextFiles: FileList | null) {
    if (!isAuthenticated) {
      return;
    }

    const selected = Array.from(nextFiles || []);
    const combined = [...files, ...selected];

    if (combined.length > 3) {
      setFormError("Можно загрузить не больше 3 фото.");
      setFiles(combined.slice(0, 3));
      return;
    }

    setFormError(null);
    setFiles(combined);
  }

  function removeFile(indexToRemove: number) {
    setFiles((currentFiles) => currentFiles.filter((_, index) => index !== indexToRemove));
    setFormError(null);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (!isAuthenticated) {
      setFormError("Чтобы предложить обмен, пожалуйста, зарегистрируйтесь");
      return;
    }

    setFormError(null);
    setSubmitState("idle");

    const trimmedTitle = title.trim();
    const trimmedDescription = description.trim();
    const trimmedCity = city.trim();
    const trimmedParticipantName = participantPublicName.trim();

    if (!trimmedTitle) {
      setFormError("Введите название.");
      return;
    }

    if (trimmedTitle.length < 2) {
      setFormError("Название должно быть не короче 2 символов.");
      return;
    }

    if (trimmedTitle.length > 255) {
      setFormError("Название должно быть не длиннее 255 символов.");
      return;
    }

    if (!trimmedDescription) {
      setFormError("Введите описание.");
      return;
    }

    if (trimmedDescription.length < 10) {
      setFormError("Описание должно быть не короче 10 символов.");
      return;
    }

    if (!trimmedCity) {
      setFormError("Укажите город.");
      return;
    }

    if (trimmedCity.length > 100) {
      setFormError("Название города должно быть не длиннее 100 символов.");
      return;
    }

    if (trimmedParticipantName.length > 255) {
      setFormError("Имя участника должно быть не длиннее 255 символов.");
      return;
    }

    const value = parseDeclaredValue(declaredValue);

    if (value === null) {
      setFormError("Укажите оценку в рублях.");
      return;
    }

    if (!Number.isFinite(value)) {
      setFormError("Оценка должна быть целым числом без букв и знаков.");
      return;
    }

    if (offerType === "physical_item" && files.length === 0) {
      setFormError("Для физического предмета нужно минимум одно фото.");
      return;
    }

    if (files.length > 3) {
      setFormError("Можно загрузить не больше 3 фото.");
      return;
    }

    setSubmitState("submitting");

    try {
      const uploaded = await Promise.all(files.map((file) => uploadImage(file)));
      const response = await createOffer({
        messenger_type: "web",
        external_user_id: externalUserId,
        username: null,
        first_name: null,
        last_name: null,
        title: trimmedTitle,
        description: trimmedDescription,
        offer_type: offerType,
        city: trimmedCity,
        declared_value: value,
        exchange_preference: exchangePreference,
        participant_public_name: trimmedParticipantName || null,
        participant_visible: participantVisible,
        consent_accepted: true,
        photo_urls: uploaded.map((item) => item.photo_url),
        photo_thumbnail_urls: uploaded.map((item) => item.thumbnail_url),
        photo_widths: uploaded.map((item) => item.width),
        photo_heights: uploaded.map((item) => item.height),
        photo_thumbnail_widths: uploaded.map((item) => item.thumbnail_width),
        photo_thumbnail_heights: uploaded.map((item) => item.thumbnail_height),
        photo_size_bytes: uploaded.map((item) => item.size_bytes),
        photo_thumbnail_size_bytes: uploaded.map((item) => item.thumbnail_size_bytes),
      });

      if (!("id" in response)) {
        setSubmitState("error");
        setFormError(response.message);
        return;
      }

      setCreatedOfferId(response.id);
      setSubmitState("success");
      setTitle("");
      setDescription("");
      setOfferType("physical_item");
      setCity("");
      setDeclaredValue("");
      setExchangePreference("any_offer");
      setParticipantPublicName("");
      setParticipantVisible(true);
      setFiles([]);
    } catch (error) {
      setSubmitState("error");
      setFormError(
        error instanceof Error
          ? error.message
          : "Не удалось отправить оффер. Проверьте backend и попробуйте ещё раз.",
      );
    }
  }

  const formDisabled = !authChecked || !isAuthenticated || submitState === "submitting";

  return (
    <section className="form-section">
      <div className="section-heading">
        <div>
          <h1>Предложить обмен</h1>
          <p className="muted">Предложение отправится на модерацию.</p>
        </div>
      </div>

      {authChecked && !isAuthenticated && (
        <div className="notice">
          <p>Чтобы предложить обмен, пожалуйста, зарегистрируйтесь</p>
          <div className="actions">
            <Link className="primary-link" to="/register">Зарегистрироваться</Link>
            <Link to="/login">Войти</Link>
          </div>
        </div>
      )}

      <form className="offer-form" onSubmit={handleSubmit}>
        <fieldset className="form-fieldset" disabled={formDisabled}>
          <label>
            Название
            <input value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>

          <label>
            Описание
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={5}
            />
          </label>

          <div className="form-row">
            <label>
              Тип
              <select
                value={offerType}
                onChange={(event) =>
                  setOfferType(event.target.value as "physical_item" | "service")
                }
              >
                <option value="physical_item">Физический предмет</option>
                <option value="service">Услуга</option>
              </select>
            </label>

            <label>
              Город
              <input value={city} onChange={(event) => setCity(event.target.value)} />
            </label>
          </div>

          <div className="form-row">
            <label>
              Оценка, ₽
              <input
                inputMode="numeric"
                value={declaredValue}
                onChange={(event) => setDeclaredValue(event.target.value)}
              />
            </label>

            <label>
              Предпочтение
              <select
                value={exchangePreference}
                onChange={(event) =>
                  setExchangePreference(
                    event.target.value as "any_offer" | "comparable_value_only",
                  )
                }
              >
                <option value="any_offer">Любое предложение</option>
                <option value="comparable_value_only">Сопоставимая ценность</option>
              </select>
            </label>
          </div>

          <label>
            Имя участника
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
            Показывать имя публично
          </label>

          <label>
            Фото
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              onChange={(event) => handleFiles(event.target.files)}
            />
          </label>
        </fieldset>

        <p className="meta">Выбрано фото: {files.length}/3</p>
        {files.length > 0 && (
          <div className="selected-photo-list">
            {files.map((file, index) => (
              <div className="selected-photo-row" key={`${file.name}-${file.lastModified}-${index}`}>
                <span>{file.name}</span>
                <button
                  className="secondary-button"
                  disabled={!isAuthenticated}
                  onClick={() => removeFile(index)}
                  type="button"
                >
                  Удалить
                </button>
              </div>
            ))}
          </div>
        )}

        {formError && <p className="notice error">{formError}</p>}
        {submitState === "success" && (
          <p className="notice success">
            Оффер создан и отправлен на модерацию.
            {createdOfferId ? ` ID: ${createdOfferId}` : ""}
          </p>
        )}

        <div className="actions">
          <button disabled={formDisabled} type="submit">
            {submitState === "submitting" ? "Отправляем..." : "Отправить"}
          </button>
          <Link to="/">Вернуться к истории обменов</Link>
        </div>
      </form>
    </section>
  );
}
