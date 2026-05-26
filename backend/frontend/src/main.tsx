import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";

import { OfferDetailPage } from "./pages/OfferDetailPage";
import { OffersPage } from "./pages/OffersPage";
import { NewOfferPage } from "./pages/NewOfferPage";
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
          <Link to="/">Каталог</Link>
          <Link to="/new-offer">Подать оффер</Link>
          <Link to="/admin/offers">Админка</Link>
        </nav>
      </header>

      <main className="page">
        <Routes>
          <Route path="/" element={<OffersPage />} />
          <Route path="/offers/:offerId" element={<OfferDetailPage />} />
          <Route path="/new-offer" element={<NewOfferPage />} />
          <Route path="/admin/offers" element={<AdminOffersPage />} />
          <Route path="/admin/offers/:offerId" element={<AdminOfferDetailPage />} />
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
