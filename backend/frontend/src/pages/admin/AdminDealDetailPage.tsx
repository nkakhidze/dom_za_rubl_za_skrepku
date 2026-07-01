import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { AdminDealDetail, getAdminDealById, updateDealStatus } from "../../api/client";

const DEAL_STATUSES = ["new", "accepted", "rejected", "completed", "cancelled"];

function ownerLabel(owner: AdminDealDetail["offer_owner"]) {
  if (!owner) {
    return "-";
  }

  const messengers = owner.messenger_accounts
    .map((account) => `${account.messenger_type}: ${account.external_user_id}`)
    .join(", ");

  return `${owner.display_name || owner.id}${owner.phone ? ` · ${owner.phone}` : ""}${
    messengers ? ` · ${messengers}` : ""
  }`;
}

export function AdminDealDetailPage() {
  const { dealId } = useParams();
  const [deal, setDeal] = useState<AdminDealDetail | null>(null);
  const [statusValue, setStatusValue] = useState("new");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function loadDeal() {
    if (!dealId) {
      setError("Сделка не найдена.");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const loadedDeal = await getAdminDealById(dealId);
      setDeal(loadedDeal);
      setStatusValue(loadedDeal.status);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить сделку.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadDeal();
  }, [dealId]);

  async function submitStatus(event: FormEvent) {
    event.preventDefault();

    if (!dealId) {
      return;
    }

    setError(null);
    setNotice(null);

    try {
      const updatedDeal = await updateDealStatus(dealId, statusValue);
      setDeal(updatedDeal);
      setStatusValue(updatedDeal.status);
      setNotice("Статус сделки обновлён.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Не удалось сохранить статус.");
    }
  }

  if (isLoading) {
    return <p className="muted">Загружаем сделку...</p>;
  }

  if (!deal) {
    return (
      <section>
        <p className="notice error">{error || "Сделка не найдена."}</p>
        <Link to="/admin/deals">Вернуться к сделкам</Link>
      </section>
    );
  }

  return (
    <section className="admin-detail">
      <Link to="/admin/deals">← Все сделки</Link>
      <div className="section-heading">
        <div>
          <h1>Сделка {deal.id.slice(0, 8)}</h1>
          <p className="meta">
            {deal.status_label || deal.status} · {new Date(deal.created_at).toLocaleDateString("ru-RU")}
          </p>
        </div>
      </div>

      {error && <p className="notice error">{error}</p>}
      {notice && <p className="notice success">{notice}</p>}

      <div className="admin-layout">
        <div>
          <section className="admin-panel">
            <h2>Сделка</h2>
            <dl className="field-list">
              <div>
                <dt>id</dt>
                <dd>{deal.id}</dd>
              </div>
              <div>
                <dt>status</dt>
                <dd>{deal.status_label || deal.status}</dd>
              </div>
              <div>
                <dt>created_at</dt>
                <dd>{new Date(deal.created_at).toLocaleString("ru-RU")}</dd>
              </div>
            </dl>
          </section>

          <section className="admin-panel">
            <h2>Оффер</h2>
            {deal.offer ? (
              <>
                <h3>{deal.offer.title}</h3>
                <p>{deal.offer.description}</p>
                <p className="meta">
                  {deal.offer.city || "-"} · {deal.offer.status} ·{" "}
                  {deal.offer.is_public ? "public" : "private"} · {deal.offer.public_value ?? "-"}
                </p>
                {deal.offer.photo_urls.length > 0 && (
                  <div className="gallery">
                    {deal.offer.photo_urls.map((url) => (
                      <img src={url} alt={deal.offer?.title || "offer"} key={url} />
                    ))}
                  </div>
                )}
              </>
            ) : (
              <p className="muted">Оффер не привязан.</p>
            )}
          </section>

          <section className="admin-panel">
            <h2>Предложенный item</h2>
            <h3>{deal.item.title}</h3>
            <p>{deal.item.description || "-"}</p>
            <p className="meta">{deal.item.status}</p>
          </section>
        </div>

        <div>
          <section className="admin-panel">
            <h2>Участники</h2>
            <p>
              <strong>Владелец оффера:</strong> {ownerLabel(deal.offer_owner)}
            </p>
            <p>
              <strong>Владелец item:</strong> {ownerLabel(deal.item_owner)}
            </p>
          </section>

          <form className="admin-panel offer-form" onSubmit={submitStatus}>
            <h2>Статус сделки</h2>
            <label>
              status
              <select value={statusValue} onChange={(event) => setStatusValue(event.target.value)}>
                {DEAL_STATUSES.map((status) => (
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
