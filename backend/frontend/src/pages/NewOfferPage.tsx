import { FormEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { createOffer, uploadImage } from "../api/client";
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

  function handleFiles(nextFiles: FileList | null) {
    const selected = Array.from(nextFiles || []);

    if (selected.length > 3) {
      setFormError("Можно загрузить не больше 3 фото.");
      setFiles(selected.slice(0, 3));
      return;
    }

    setFormError(null);
    setFiles(selected);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
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

  return (
    <section className="form-section">
      <div className="section-heading">
        <div>
          <h1>Подать оффер</h1>
          <p className="muted">Предложение отправится на модерацию.</p>
        </div>
      </div>

      <form className="offer-form" onSubmit={handleSubmit}>
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
        <p className="meta">Выбрано фото: {files.length}/3</p>

        {formError && <p className="notice error">{formError}</p>}
        {submitState === "success" && (
          <p className="notice success">
            Оффер создан и отправлен на модерацию.
            {createdOfferId ? ` ID: ${createdOfferId}` : ""}
          </p>
        )}

        <div className="actions">
          <button disabled={submitState === "submitting"} type="submit">
            {submitState === "submitting" ? "Отправляем..." : "Отправить"}
          </button>
          <Link to="/">Вернуться к истории обменов</Link>
        </div>
      </form>
    </section>
  );
}
