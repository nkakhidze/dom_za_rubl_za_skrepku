import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";

import { AuthUser, getAdminToken, getMe } from "./api/client";
import { AccountPage } from "./pages/AccountPage";
import { LegalDocumentPage } from "./pages/LegalDocumentPage";
import { OfferDetailPage } from "./pages/OfferDetailPage";
import { OffersPage } from "./pages/OffersPage";
import { PublicItemPage } from "./pages/PublicItemPage";
import { NewOfferPage } from "./pages/NewOfferPage";
import { MyDealsPage } from "./pages/MyDealsPage";
import { MyItemsPage } from "./pages/MyItemsPage";
import { RegisterPage } from "./pages/RegisterPage";
import { UserLoginPage } from "./pages/UserLoginPage";
import { AdminDealDetailPage } from "./pages/admin/AdminDealDetailPage";
import { AdminDealsPage } from "./pages/admin/AdminDealsPage";
import { AdminItemsPage } from "./pages/admin/AdminItemsPage";
import { AdminLoginPage } from "./pages/admin/AdminLoginPage";
import { AdminOfferDetailPage } from "./pages/admin/AdminOfferDetailPage";
import { AdminOffersPage } from "./pages/admin/AdminOffersPage";
import "./styles.css";


function App() {
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    function refreshCurrentUser() {
      if (!getAdminToken()) {
        setCurrentUser(null);
        return;
      }

      getMe()
        .then(setCurrentUser)
        .catch(() => setCurrentUser(null));
    }

    refreshCurrentUser();
    window.addEventListener("paperclip-admin-token-changed", refreshCurrentUser);

    return () => {
      window.removeEventListener("paperclip-admin-token-changed", refreshCurrentUser);
    };
  }, []);

  const canSeeAdminLinks =
    currentUser?.roles.some((role) =>
      ["editor", "moderator", "admin", "super_admin"].includes(role),
    ) || false;

  return (
    <BrowserRouter>
      <header className="topbar">
        <Link className="brand" to="/">
          Дом за скрепку
        </Link>
        <nav>
          <Link to="/">История обменов</Link>
          <Link to="/new-offer">Предложить обмен</Link>
          <Link to="/my/items">Мои предложения</Link>
          <Link to="/my/deals">Мои сделки</Link>
          {canSeeAdminLinks && (
            <>
              <Link to="/admin/offers">Заявки</Link>
              <Link to="/admin/items">Предметы</Link>
              <Link to="/admin/deals">Сделки</Link>
            </>
          )}
          {currentUser ? <Link to="/account">Личный кабинет</Link> : <Link to="/login">Войти</Link>}
        </nav>
      </header>

      <main className="page">
        <Routes>
          <Route path="/" element={<OffersPage />} />
          <Route path="/items/:itemId" element={<PublicItemPage />} />
          <Route path="/offers/:offerId" element={<OfferDetailPage />} />
          <Route path="/new-offer" element={<NewOfferPage />} />
          <Route path="/login" element={<UserLoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/account" element={<AccountPage />} />
          <Route path="/legal/:documentSlug" element={<LegalDocumentPage />} />
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
