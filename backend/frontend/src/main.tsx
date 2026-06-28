import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";

import { OfferDetailPage } from "./pages/OfferDetailPage";
import { OffersPage } from "./pages/OffersPage";
import { NewOfferPage } from "./pages/NewOfferPage";
import { MyDealsPage } from "./pages/MyDealsPage";
import { MyItemsPage } from "./pages/MyItemsPage";
import { AdminDealDetailPage } from "./pages/admin/AdminDealDetailPage";
import { AdminDealsPage } from "./pages/admin/AdminDealsPage";
import { AdminItemsPage } from "./pages/admin/AdminItemsPage";
import { AdminLoginPage } from "./pages/admin/AdminLoginPage";
import { AdminOfferDetailPage } from "./pages/admin/AdminOfferDetailPage";
import { AdminOffersPage } from "./pages/admin/AdminOffersPage";
import "./styles.css";

function App() {
  return (
    <BrowserRouter>
      <header className="topbar">
        <Link className="brand" to="/">
          Дом за рубль за скрепку
        </Link>
        <nav>
          <Link to="/">История обменов</Link>
          <Link to="/new-offer">Подать оффер</Link>
          <Link to="/my/items">Мои предметы</Link>
          <Link to="/my/deals">Мои сделки</Link>
          <Link to="/admin/offers">Заявки</Link>
          <Link to="/admin/items">Предметы</Link>
          <Link to="/admin/deals">Сделки</Link>
          <Link to="/admin/login">Войти</Link>
        </nav>
      </header>

      <main className="page">
        <Routes>
          <Route path="/" element={<OffersPage />} />
          <Route path="/offers/:offerId" element={<OfferDetailPage />} />
          <Route path="/new-offer" element={<NewOfferPage />} />
          <Route path="/my/items" element={<MyItemsPage />} />
          <Route path="/my/deals" element={<MyDealsPage />} />
          <Route path="/admin/offers" element={<AdminOffersPage />} />
          <Route path="/admin/offers/:offerId" element={<AdminOfferDetailPage />} />
          <Route path="/admin/items" element={<AdminItemsPage />} />
          <Route path="/admin/deals" element={<AdminDealsPage />} />
          <Route path="/admin/deals/:dealId" element={<AdminDealDetailPage />} />
          <Route path="/admin/login" element={<AdminLoginPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
