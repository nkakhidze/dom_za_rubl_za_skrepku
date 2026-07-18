import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  getPublicCurrentItem,
  getPublicExchangeChain,
  PublicCurrentItem,
  PublicExchangeChainItem,
} from "../api/client";

type ChainItem = {
  id: string;
  title: string;
  description: string | null;
  public_story: string | null;
  photo_url: string | null;
  photo_urls: string[];
  thumbnail_url: string | null;
  thumbnail_urls: string[];
};

type ChainNode = {
  item: ChainItem;
  incomingDeal: PublicExchangeChainItem | null;
};

function getItemPreviewUrl(item: ChainNode["item"]) {
  return item.thumbnail_urls[0] || item.thumbnail_url || item.photo_urls[0] || item.photo_url;
}

function hasPublicText(value: string | null | undefined) {
  const text = (value || "").trim();

  return Boolean(text) && text !== "-";
}

function formatDealDate(value: string | null) {
  if (!value) {
    return "дата не указана";
  }

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date(value));
}

function currentItemToChainItem(item: PublicCurrentItem): ChainItem {
  const thumbnailUrl = item.thumbnail_urls[0] || item.photo_url;

  return {
    id: item.id,
    title: item.title,
    description: item.description,
    public_story: item.public_story,
    photo_url: item.photo_url,
    photo_urls: item.photo_url ? [item.photo_url] : [],
    thumbnail_url: thumbnailUrl,
    thumbnail_urls: item.thumbnail_urls.length > 0 ? item.thumbnail_urls : thumbnailUrl ? [thumbnailUrl] : [],
  };
}

function buildChainNodes(
  deals: PublicExchangeChainItem[],
  currentItem: PublicCurrentItem | null,
): ChainNode[] {
  if (deals.length === 0) {
    return currentItem
      ? [
          {
            item: currentItemToChainItem(currentItem),
            incomingDeal: null,
          },
        ]
      : [];
  }

  return [
    {
      item: deals[0].given_item,
      incomingDeal: null,
    },
    ...deals.map((deal) => ({
      item: deal.received_item,
      incomingDeal: deal,
    })),
  ];
}

export function OffersPage() {
  const [deals, setDeals] = useState<PublicExchangeChainItem[]>([]);
  const [currentItem, setCurrentItem] = useState<PublicCurrentItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getPublicExchangeChain(),
      getPublicCurrentItem().catch(() => null),
    ])
      .then(([loadedDeals, loadedCurrentItem]) => {
        setDeals(loadedDeals);
        setCurrentItem(loadedCurrentItem);
      })
      .catch(() =>
        setError("Не удалось загрузить историю обменов. Попробуйте позже."),
      )
      .finally(() => setIsLoading(false));
  }, []);

  const chainNodes = useMemo(() => buildChainNodes(deals, currentItem).reverse(), [deals, currentItem]);

  if (isLoading) {
    return <p className="muted">Загружаем историю обменов...</p>;
  }

  if (error) {
    return <p className="notice error">{error}</p>;
  }

  return (
    <section>
      <div className="section-heading">
        <div>
          <h1>История обменов</h1>
        </div>
        <Link className="primary-link" to="/new-offer">
          Предложить обмен
        </Link>
      </div>

      {chainNodes.length === 0 ? (
        <p className="notice">История обменов пока не опубликована.</p>
      ) : (
        <div className="item-chain">
          {chainNodes.map((node, index) => (
            <article className="offer-card chain-node-card" key={`${node.item.id}-${index}`}>
              <div className="thumb exchange-thumb">
                <Link className="thumb-link" to={`/items/${node.item.id}`}>
                  {getItemPreviewUrl(node.item) ? (
                    <img src={getItemPreviewUrl(node.item) || ""} alt={node.item.title} />
                  ) : (
                    <span>Нет фото</span>
                  )}
                </Link>
              </div>
              <div className="offer-card-body">
                <h2>
                  <Link to={`/items/${node.item.id}`}>{node.item.title}</Link>
                </h2>
                {hasPublicText(node.item.description) && <p>{node.item.description}</p>}
                {hasPublicText(node.item.public_story) && <p>{node.item.public_story}</p>}

                {node.incomingDeal && (
                  <div className="exchange-meta">
                    {node.incomingDeal.participant_visible &&
                      node.incomingDeal.participant_public_name && (
                        <p className="meta">
                          Участник: {node.incomingDeal.participant_public_name}
                        </p>
                      )}
                    <p className="meta">
                      Дата обмена: {formatDealDate(node.incomingDeal.deal_date)}
                    </p>
                    {node.incomingDeal.video_url && (
                      <a href={node.incomingDeal.video_url} rel="noreferrer" target="_blank">
                        Смотреть видео
                      </a>
                    )}
                  </div>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
