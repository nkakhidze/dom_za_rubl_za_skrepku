import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getPublicItemById, PublicItemDetail } from "../api/client";

const PLATFORM_LINKS: Array<[keyof PublicItemDetail, string, string]> = [
  ["vk_url", "VK", "ВКонтакте"],
  ["tiktok_url", "♫", "TikTok"],
  ["youtube_url", "▶", "YouTube"],
  ["dzen_url", "Д", "Дзен"],
  ["rutube_url", "R", "Rutube"],
  ["instagram_url", "◎", "Instagram"],
];

export function PublicItemPage() {
  const { itemId } = useParams();
  const [item, setItem] = useState<PublicItemDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activePhotoIndex, setActivePhotoIndex] = useState<number | null>(null);

  useEffect(() => {
    if (!itemId) {
      setError("Предмет не найден.");
      setIsLoading(false);
      return;
    }

    getPublicItemById(itemId)
      .then(setItem)
      .catch(() => setError("Не удалось загрузить предмет. Попробуйте позже."))
      .finally(() => setIsLoading(false));
  }, [itemId]);

  useEffect(() => {
    if (activePhotoIndex === null) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setActivePhotoIndex(null);
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [activePhotoIndex]);

  if (isLoading) {
    return <p className="muted">Загружаем предмет...</p>;
  }

  if (!item) {
    return (
      <section>
        <p className="notice error">{error || "Предмет не найден."}</p>
        <Link to="/">Вернуться к истории обменов</Link>
      </section>
    );
  }

  const photos = item.photo_urls.length > 0 ? item.photo_urls : item.photo_url ? [item.photo_url] : [];
  const activePhoto = activePhotoIndex === null ? null : photos[activePhotoIndex];
  const links = PLATFORM_LINKS.filter(([field]) => item[field]);

  function showPreviousPhoto() {
    setActivePhotoIndex((current) =>
      current === null ? null : current === 0 ? photos.length - 1 : current - 1,
    );
  }

  function showNextPhoto() {
    setActivePhotoIndex((current) =>
      current === null ? null : current === photos.length - 1 ? 0 : current + 1,
    );
  }

  function showNextPhotoOrClose() {
    setActivePhotoIndex((current) =>
      current === null ? null : current >= photos.length - 1 ? null : current + 1,
    );
  }

  return (
    <section>
      <Link to="/">← История обменов</Link>
      <div className="section-heading">
        <div>
          <h1>{item.title}</h1>
          {item.description && <p className="muted">{item.description}</p>}
        </div>
      </div>

      {item.public_story && <p className="item-story">{item.public_story}</p>}

      {photos.length === 0 ? (
        <p className="notice">Нет фото.</p>
      ) : (
        <div className="item-photo-grid">
          {photos.map((photoUrl, index) => (
            <button
              className="item-photo-button"
              key={`${photoUrl}-${index}`}
              onClick={() => setActivePhotoIndex(index)}
              type="button"
            >
              <img src={photoUrl} alt={item.title} />
            </button>
          ))}
        </div>
      )}

      {links.length > 0 && (
        <div className="platform-links">
          {links.map(([field, icon, label]) => (
            <p className="platform-link" key={field}>
              <span aria-label={label} title={label}>
                {icon}
              </span>
              <span>—</span>
              <a href={item[field] as string} rel="noreferrer" target="_blank">
                {item[field] as string}
              </a>
            </p>
          ))}
        </div>
      )}

      {activePhoto && (
        <div className="fullscreen-gallery" role="dialog" aria-modal="true">
          <button
            className="fullscreen-close"
            onClick={() => setActivePhotoIndex(null)}
            type="button"
          >
            Закрыть
          </button>
          {photos.length > 1 && (
            <button className="gallery-arrow gallery-arrow-left" onClick={showPreviousPhoto} type="button">
              ←
            </button>
          )}
          <img
            src={activePhoto}
            alt={item.title}
            onClick={showNextPhotoOrClose}
            role="button"
          />
          {photos.length > 1 && (
            <button className="gallery-arrow gallery-arrow-right" onClick={showNextPhoto} type="button">
              →
            </button>
          )}
        </div>
      )}
    </section>
  );
}
