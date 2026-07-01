import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  getPublicExchangeChain,
  PublicExchangeChainItem,
} from "../api/client";

type ChainNode = {
  item: PublicExchangeChainItem["given_item"];
  incomingDeal: PublicExchangeChainItem | null;
};

function getItemPreviewUrl(item: ChainNode["item"]) {
  return item.thumbnail_urls[0] || item.thumbnail_url || item.photo_urls[0] || item.photo_url;
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

function buildChainNodes(deals: PublicExchangeChainItem[]): ChainNode[] {
  if (deals.length === 0) {
    return [];
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
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPublicExchangeChain()
      .then(setDeals)
      .catch(() =>
        setError("Не удалось загрузить историю обменов. Попробуйте позже."),
      )
      .finally(() => setIsLoading(false));
  }, []);

  const chainNodes = useMemo(() => buildChainNodes(deals).reverse(), [deals]);

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
                {node.item.description && <p>{node.item.description}</p>}

                {node.incomingDeal && (
                  <div className="exchange-meta">
                    {node.incomingDeal.public_story && (
                      <p>{node.incomingDeal.public_story}</p>
                    )}
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
