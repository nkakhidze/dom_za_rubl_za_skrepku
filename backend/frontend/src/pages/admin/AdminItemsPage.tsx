import { FormEvent, useEffect, useState } from "react";

import {
  addAdminItemPhoto,
  AdminItem,
  deleteAdminItemPhoto,
  getAdminItems,
  updateAdminItem,
  uploadImage,
} from "../../api/client";

const ITEM_TYPE_LABELS: Record<string, string> = {
  physical_item: "Физический предмет",
  service: "Услуга",
  money: "Деньги",
};

const ITEM_STATUS_LABELS: Record<string, string> = {
  active: "Активный",
  archived: "В архиве",
  current: "Текущий",
  past: "Прошлый",
  final: "Финальный",
  planned: "Запланирован",
};

const OWNER_TYPE_LABELS: Record<string, string> = {
  personal: "Пользователь",
  tom_sawyer_fest: "Том Сойер Фест",
  partner_org: "Партнёр",
  other: "Другое",
};

const PLATFORM_FIELDS = [
  ["vkUrl", "ВКонтакте"],
  ["tiktokUrl", "TikTok"],
  ["youtubeUrl", "YouTube"],
  ["dzenUrl", "Дзен"],
  ["rutubeUrl", "Rutube"],
  ["instagramUrl", "Instagram"],
] as const;

type EditForm = {
  title: string;
  description: string;
  itemType: "physical_item" | "service" | "money";
  status: string;
  internalValue: string;
  valuationSource: string;
  ownerType: "personal" | "tom_sawyer_fest" | "partner_org" | "other";
  ownerName: string;
  publicStory: string;
  sequenceNumber: string;
  isCurrent: boolean;
  isPublic: boolean;
  vkUrl: string;
  tiktokUrl: string;
  youtubeUrl: string;
  dzenUrl: string;
  rutubeUrl: string;
  instagramUrl: string;
};

function numberOrNull(value: string): number | null {
  if (!value.trim()) {
    return null;
  }

  return Number(value);
}

function buildEditForm(item: AdminItem): EditForm {
  return {
    title: item.title,
    description: item.description || "",
    itemType: item.item_type as "physical_item" | "service" | "money",
    status: item.status,
    internalValue: item.internal_value?.toString() || "",
    valuationSource: item.valuation_source || "",
    ownerType: item.owner_type as "personal" | "tom_sawyer_fest" | "partner_org" | "other",
    ownerName: item.owner_name || "",
    publicStory: item.public_story || "",
    sequenceNumber: item.sequence_number?.toString() || "",
    isCurrent: item.is_current,
    isPublic: item.is_public,
    vkUrl: item.vk_url || "",
    tiktokUrl: item.tiktok_url || "",
    youtubeUrl: item.youtube_url || "",
    dzenUrl: item.dzen_url || "",
    rutubeUrl: item.rutube_url || "",
    instagramUrl: item.instagram_url || "",
  };
}

export function AdminItemsPage() {
  const [items, setItems] = useState<AdminItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<EditForm | null>(null);
  const [newPhotoFiles, setNewPhotoFiles] = useState<File[]>([]);

  async function loadItems() {
    setIsLoading(true);
    setError(null);

    try {
      setItems(await getAdminItems());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить предметы.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadItems();
  }, []);

  function startEdit(item: AdminItem) {
    setError(null);
    setNotice(null);
    setNewPhotoFiles([]);
    setEditingItemId(item.id);
    setEditForm(buildEditForm(item));
  }

  function updateEditForm(patch: Partial<EditForm>) {
    setEditForm((current) => (current ? { ...current, ...patch } : current));
  }

  async function submitEdit(event: FormEvent) {
    event.preventDefault();

    if (!editingItemId || !editForm) {
      return;
    }

    setError(null);
    setNotice(null);

    try {
      await updateAdminItem(editingItemId, {
        title: editForm.title.trim(),
        description: editForm.description.trim() || null,
        item_type: editForm.itemType,
        status: editForm.status,
        internal_value: numberOrNull(editForm.internalValue),
        valuation_source: editForm.valuationSource.trim() || null,
        owner_type: editForm.ownerType,
        owner_name: editForm.ownerName.trim() || null,
        is_current: editForm.isCurrent,
        is_public: editForm.isPublic,
        public_story: editForm.publicStory.trim() || null,
        sequence_number: numberOrNull(editForm.sequenceNumber),
        vk_url: editForm.vkUrl.trim() || null,
        tiktok_url: editForm.tiktokUrl.trim() || null,
        youtube_url: editForm.youtubeUrl.trim() || null,
        dzen_url: editForm.dzenUrl.trim() || null,
        rutube_url: editForm.rutubeUrl.trim() || null,
        instagram_url: editForm.instagramUrl.trim() || null,
      });
      setNotice("Предмет сохранён.");
      setEditingItemId(null);
      setEditForm(null);
      await loadItems();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Не удалось сохранить предмет.");
    }
  }

  function handleNewPhotoFiles(nextFiles: FileList | null) {
    setNewPhotoFiles(Array.from(nextFiles || []));
  }

  async function addPhotos(itemId: string) {
    if (newPhotoFiles.length === 0) {
      setError("Выберите хотя бы одно фото.");
      return;
    }

    setError(null);
    setNotice(null);

    try {
      const uploaded = await Promise.all(newPhotoFiles.map((file) => uploadImage(file)));

      for (const photo of uploaded) {
        await addAdminItemPhoto(itemId, {
          photo_url: photo.photo_url,
          thumbnail_url: photo.thumbnail_url,
          width: photo.width,
          height: photo.height,
          thumbnail_width: photo.thumbnail_width,
          thumbnail_height: photo.thumbnail_height,
          size_bytes: photo.size_bytes,
          thumbnail_size_bytes: photo.thumbnail_size_bytes,
        });
      }

      setNewPhotoFiles([]);
      setNotice(uploaded.length === 1 ? "Фото добавлено." : "Фотографии добавлены.");
      await loadItems();
    } catch (photoError) {
      setError(photoError instanceof Error ? photoError.message : "Не удалось добавить фотографии.");
    }
  }

  async function deletePhoto(itemId: string, photoId: string) {
    setError(null);
    setNotice(null);

    try {
      await deleteAdminItemPhoto(itemId, photoId);
      setNotice("Фото удалено.");
      await loadItems();
    } catch (photoError) {
      setError(photoError instanceof Error ? photoError.message : "Не удалось удалить фото.");
    }
  }

  return (
    <section>
      <div className="section-heading">
        <div>
          <h1>Предметы цепочки</h1>
          <p className="muted">
            Список отсортирован от текущего предмета к началу цепочки.
          </p>
        </div>
        <button type="button" onClick={() => void loadItems()}>
          Обновить
        </button>
      </div>

      {error && <p className="notice error">{error}</p>}
      {notice && <p className="notice success">{notice}</p>}

      <section className="admin-panel">
        <h2>Все предметы</h2>
        {isLoading && <p className="muted">Загружаем предметы...</p>}
        {!isLoading && items.length === 0 ? (
          <p className="notice">Предметов пока нет.</p>
        ) : (
          <div className="admin-list">
            {items.map((item) => (
              <article className="admin-row" key={item.id}>
                <div className="admin-thumb">
                  {(item.thumbnail_urls[0] || item.photo_urls[0]) ? (
                    <img src={item.thumbnail_urls[0] || item.photo_urls[0]} alt={item.title} />
                  ) : (
                    <span>Нет фото</span>
                  )}
                </div>
                <div>
                  <h3>{item.title}</h3>
                  <p className="meta">
                    №{item.sequence_number ?? "-"} · {item.id.slice(0, 8)} ·{" "}
                    {ITEM_STATUS_LABELS[item.status] || item.status} ·{" "}
                    {item.is_current ? "текущий" : "не текущий"} ·{" "}
                    {item.is_public ? "публичный" : "скрытый"}
                  </p>
                  <p className="meta">
                    цена: {item.internal_value ?? "-"} · владелец:{" "}
                    {item.owner_name || OWNER_TYPE_LABELS[item.owner_type] || item.owner_type}
                  </p>
                  {item.source_offer_id && (
                    <p className="meta">заявка-источник: {item.source_offer_id}</p>
                  )}
                  {item.description && <p>{item.description}</p>}

                  {editingItemId === item.id && editForm ? (
                    <form className="offer-form inline-edit-form" onSubmit={submitEdit}>
                      <label>
                        Название
                        <input
                          value={editForm.title}
                          onChange={(event) => updateEditForm({ title: event.target.value })}
                          required
                        />
                      </label>
                      <label>
                        Описание
                        <textarea
                          value={editForm.description}
                          onChange={(event) => updateEditForm({ description: event.target.value })}
                          rows={3}
                        />
                      </label>
                      <div className="form-row">
                        <label>
                          Тип
                          <select
                            value={editForm.itemType}
                            onChange={(event) =>
                              updateEditForm({
                                itemType: event.target.value as "physical_item" | "service" | "money",
                              })
                            }
                          >
                            <option value="physical_item">Физический предмет</option>
                            <option value="service">Услуга</option>
                            <option value="money">Деньги</option>
                          </select>
                        </label>
                        <label>
                          Статус
                          <select
                            value={editForm.status}
                            onChange={(event) => updateEditForm({ status: event.target.value })}
                          >
                            <option value="current">Текущий</option>
                            <option value="past">Прошлый</option>
                            <option value="final">Финальный</option>
                            <option value="planned">Запланирован</option>
                            <option value="active">Активный</option>
                            <option value="archived">В архиве</option>
                          </select>
                        </label>
                      </div>
                      <div className="form-row">
                        <label>
                          Цена
                          <input
                            inputMode="numeric"
                            value={editForm.internalValue}
                            onChange={(event) => updateEditForm({ internalValue: event.target.value })}
                          />
                        </label>
                        <label>
                          Порядковый номер
                          <input
                            inputMode="numeric"
                            value={editForm.sequenceNumber}
                            onChange={(event) => updateEditForm({ sequenceNumber: event.target.value })}
                          />
                        </label>
                      </div>
                      <div className="form-row">
                        <label>
                          Тип владельца
                          <select
                            value={editForm.ownerType}
                            onChange={(event) =>
                              updateEditForm({
                                ownerType: event.target.value as "personal" | "tom_sawyer_fest" | "partner_org" | "other",
                              })
                            }
                          >
                            <option value="personal">Пользователь</option>
                            <option value="tom_sawyer_fest">Том Сойер Фест</option>
                            <option value="partner_org">Партнёр</option>
                            <option value="other">Другое</option>
                          </select>
                        </label>
                        <label>
                          Публикуемое имя владельца
                          <input
                            value={editForm.ownerName}
                            onChange={(event) => updateEditForm({ ownerName: event.target.value })}
                          />
                        </label>
                      </div>
                      <label>
                        Источник оценки
                        <textarea
                          value={editForm.valuationSource}
                          onChange={(event) => updateEditForm({ valuationSource: event.target.value })}
                          rows={2}
                        />
                      </label>
                      <label>
                        Публичная история предмета
                        <textarea
                          value={editForm.publicStory}
                          onChange={(event) => updateEditForm({ publicStory: event.target.value })}
                          rows={3}
                        />
                      </label>

                      <div className="platform-edit-grid">
                        {PLATFORM_FIELDS.map(([field, label]) => (
                          <label key={field}>
                            {label}
                            <input
                              value={editForm[field]}
                              onChange={(event) => updateEditForm({ [field]: event.target.value })}
                            />
                          </label>
                        ))}
                      </div>

                      <section className="photo-admin-panel">
                        <h4>Фотографии</h4>
                        {item.photos.length === 0 ? (
                          <p className="muted">Фото пока нет.</p>
                        ) : (
                          <div className="photo-admin-grid">
                            {item.photos.map((photo) => (
                              <div className="photo-admin-item" key={photo.id}>
                                <img src={photo.thumbnail_url || photo.photo_url} alt={item.title} />
                                <button
                                  aria-label="Удалить фото"
                                  className="photo-delete-button"
                                  onClick={() => void deletePhoto(item.id, photo.id)}
                                  type="button"
                                >
                                  ×
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
                        <div className="form-row">
                          <label>
                            Добавить фото
                            <input
                              accept="image/jpeg,image/png,image/webp"
                              multiple
                              onChange={(event) => handleNewPhotoFiles(event.target.files)}
                              type="file"
                            />
                          </label>
                          <button type="button" onClick={() => void addPhotos(item.id)}>
                            Загрузить
                          </button>
                        </div>
                        {newPhotoFiles.length > 0 && (
                          <p className="meta">
                            Выбрано фото: {newPhotoFiles.map((file) => file.name).join(", ")}
                          </p>
                        )}
                      </section>

                      <label className="checkbox">
                        <input
                          checked={editForm.isCurrent}
                          onChange={(event) => updateEditForm({ isCurrent: event.target.checked })}
                          type="checkbox"
                        />
                        Текущий предмет цепочки
                      </label>
                      <label className="checkbox">
                        <input
                          checked={editForm.isPublic}
                          onChange={(event) => updateEditForm({ isPublic: event.target.checked })}
                          type="checkbox"
                        />
                        Публичный предмет
                      </label>
                      <div className="actions">
                        <button type="submit">Сохранить предмет</button>
                        <button
                          className="secondary-button"
                          type="button"
                          onClick={() => {
                            setEditingItemId(null);
                            setEditForm(null);
                          }}
                        >
                          Отмена
                        </button>
                      </div>
                    </form>
                  ) : (
                    <button className="secondary-button" type="button" onClick={() => startEdit(item)}>
                      Редактировать предмет
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </section>
  );
}
