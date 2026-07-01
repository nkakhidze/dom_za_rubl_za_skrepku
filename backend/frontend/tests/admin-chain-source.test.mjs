import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const clientSource = readFileSync(new URL("../src/api/client.ts", import.meta.url), "utf8");
const mainSource = readFileSync(new URL("../src/main.tsx", import.meta.url), "utf8");
const offersPageSource = readFileSync(
  new URL("../src/pages/admin/AdminOffersPage.tsx", import.meta.url),
  "utf8",
);
const offerDetailSource = readFileSync(
  new URL("../src/pages/admin/AdminOfferDetailPage.tsx", import.meta.url),
  "utf8",
);
const itemsPageSource = readFileSync(
  new URL("../src/pages/admin/AdminItemsPage.tsx", import.meta.url),
  "utf8",
);
const adminLoginPageSource = readFileSync(
  new URL("../src/pages/admin/AdminLoginPage.tsx", import.meta.url),
  "utf8",
);
const userLoginPageSource = readFileSync(
  new URL("../src/pages/UserLoginPage.tsx", import.meta.url),
  "utf8",
);

test("admin navigation is role-gated and user login is separate", () => {
  assert.match(mainSource, /canSeeAdminLinks/);
  assert.match(mainSource, /\/admin\/offers/);
  assert.match(mainSource, /\/admin\/items/);
  assert.match(mainSource, /\/admin\/deals/);
  assert.match(mainSource, /\/login/);
  assert.match(mainSource, /\/account/);
});

test("admin offer UI explains offers as incoming user requests", () => {
  assert.match(offersPageSource, /getAdminOffersFiltered/);
  assert.match(offersPageSource, /visibility_status/);
  assert.match(offersPageSource, /value_desc/);
});

test("admin offer detail can accept an offer into the exchange chain", () => {
  assert.match(clientSource, /selectOfferAsNext/);
  assert.match(clientSource, /\/api\/admin\/offers\/\$\{offerId\}\/select-next/);
  assert.match(offerDetailSource, /selectOfferAsNext/);
  assert.match(offerDetailSource, /window\.confirm/);
  assert.match(offerDetailSource, /getAdminItems\(\{ is_current: true \}\)/);
});

test("admin items page edits chain items and manages photos", () => {
  assert.doesNotMatch(itemsPageSource, /<h2>Создать предмет<\/h2>/);
  assert.doesNotMatch(itemsPageSource, /<h2>Текущий предмет цепочки<\/h2>/);
  assert.match(itemsPageSource, /updateAdminItem/);
  assert.match(itemsPageSource, /sequence_number/);
  assert.match(itemsPageSource, /uploadImage/);
  assert.match(itemsPageSource, /type="file"/);
  assert.match(itemsPageSource, /multiple/);
  assert.match(itemsPageSource, /addAdminItemPhoto/);
  assert.match(itemsPageSource, /thumbnail_url: photo\.thumbnail_url/);
  assert.match(itemsPageSource, /thumbnail_size_bytes: photo\.thumbnail_size_bytes/);
  assert.match(itemsPageSource, /photo\.thumbnail_url \|\| photo\.photo_url/);
  assert.match(itemsPageSource, /deleteAdminItemPhoto/);
  assert.match(itemsPageSource, /photo-delete-button/);
  assert.doesNotMatch(itemsPageSource, /URL нового фото/);
  assert.match(clientSource, /getAdminItems/);
  assert.match(clientSource, /updateAdminItem/);
});

test("admin offers page exposes request status, visibility and sorting controls", () => {
  assert.match(offersPageSource, /type="checkbox"/);
  assert.match(offersPageSource, /value_desc/);
  assert.match(offersPageSource, /visibility_status/);
});

test("auth client does not call /api/auth/me without a stored token", () => {
  assert.match(clientSource, /export function getMe\(\): Promise<AuthUser>/);
  assert.match(clientSource, /const token = getAdminToken\(\)/);
  assert.match(clientSource, /return Promise\.reject\(new Error/);
  assert.doesNotMatch(clientSource, /getMe\(\): Promise<AuthUser> \{\s*return request<AuthUser>\("\/api\/auth\/me"/);
});

test("user login exposes future account linking actions, admin login does not register employees", () => {
  assert.match(userLoginPageSource, /Войти через MAX \/ объединить аккаунты/);
  assert.match(userLoginPageSource, /Войти через Telegram \/ объединить аккаунты/);
  assert.match(userLoginPageSource, /Зарегистрироваться/);
  assert.match(userLoginPageSource, /подтверждённый сценарий связывания/);
  assert.match(adminLoginPageSource, /Войти как пользователь/);
  assert.doesNotMatch(adminLoginPageSource, /Зарегистрироваться/);
});
