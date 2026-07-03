import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const clientSource = readFileSync(new URL("../src/api/client.ts", import.meta.url), "utf8");
const mainSource = readFileSync(new URL("../src/main.tsx", import.meta.url), "utf8");
const registerPageSource = readFileSync(new URL("../src/pages/RegisterPage.tsx", import.meta.url), "utf8");
const accountPageSource = readFileSync(new URL("../src/pages/AccountPage.tsx", import.meta.url), "utf8");
const userLoginPageSource = readFileSync(new URL("../src/pages/UserLoginPage.tsx", import.meta.url), "utf8");
const legalPageSource = readFileSync(new URL("../src/pages/LegalDocumentPage.tsx", import.meta.url), "utf8");
const myItemsPageSource = readFileSync(new URL("../src/pages/MyItemsPage.tsx", import.meta.url), "utf8");
const myDealsPageSource = readFileSync(new URL("../src/pages/MyDealsPage.tsx", import.meta.url), "utf8");

test("frontend exposes user registration, account and legal routes", () => {
  assert.match(mainSource, /path="\/register"/);
  assert.match(mainSource, /path="\/account"/);
  assert.match(mainSource, /path="\/legal\/:documentSlug"/);
});

test("registration page sends required consents and optional marketing channels", () => {
  assert.match(registerPageSource, /is_adult_confirmed/);
  assert.match(registerPageSource, /user_agreement/);
  assert.match(registerPageSource, /personal_data_consent/);
  assert.match(registerPageSource, /privacy_policy_version/);
  assert.match(registerPageSource, /marketing_consent/);
  assert.match(registerPageSource, /marketingEmail/);
  assert.match(registerPageSource, /marketingTelegram/);
  assert.match(registerPageSource, /marketingMax/);
});

test("api client supports legal documents, registration and account consent updates", () => {
  assert.match(clientSource, /registerUser/);
  assert.match(clientSource, /getAccount/);
  assert.match(clientSource, /getLegalDocument/);
  assert.match(clientSource, /updateMarketingConsent/);
  assert.match(clientSource, /\/api\/auth\/register/);
  assert.match(clientSource, /\/api\/legal\/documents/);
});

test("account page updates marketing channels independently", () => {
  assert.match(accountPageSource, /updateAccount/);
  assert.match(accountPageSource, /Редактировать/);
  assert.doesNotMatch(accountPageSource, /Согласия и документы/);
  assert.doesNotMatch(accountPageSource, /updateMarketingConsent/);
});

test("legal page renders markdown without raw HTML injection", () => {
  assert.match(legalPageSource, /renderMarkdown/);
  assert.doesNotMatch(legalPageSource, /dangerouslySetInnerHTML/);
});

test("my pages use authenticated user endpoints and do not ask for user_id", () => {
  assert.match(clientSource, /getMyOffers/);
  assert.match(clientSource, /\/api\/auth\/me\/offers/);
  assert.match(clientSource, /getMyDeals/);
  assert.match(clientSource, /\/api\/auth\/me\/deals/);
  assert.match(myItemsPageSource, /getMyOffers/);
  assert.match(myDealsPageSource, /getMyDeals/);
  assert.doesNotMatch(myItemsPageSource, /user_id/);
  assert.doesNotMatch(myDealsPageSource, /user_id/);
  assert.doesNotMatch(myItemsPageSource, /createItem/);
});

test("offer creation uses current auth token when user is logged in", () => {
  assert.match(clientSource, /export function createOffer/);
  assert.match(clientSource, /const token = getAdminToken\(\)/);
  assert.match(clientSource, /Authorization: `Bearer \$\{token\}`/);
});

test("user login page starts real telegram login flow", () => {
  assert.match(clientSource, /createTelegramLoginLink/);
  assert.match(clientSource, /getTelegramLoginStatus/);
  assert.match(clientSource, /\/api\/auth\/telegram\/login-link/);
  assert.match(userLoginPageSource, /createTelegramLoginLink/);
  assert.match(userLoginPageSource, /getTelegramLoginStatus/);
  assert.match(userLoginPageSource, /У меня уже есть аккаунт сайта/);
  assert.match(userLoginPageSource, /Продолжить через Telegram/);
  assert.doesNotMatch(userLoginPageSource, /showAuthStub\("Telegram"\)/);
});

test("navigation uses proposal wording", () => {
  assert.match(mainSource, /Предложить обмен/);
  assert.match(mainSource, /Мои предложения/);
  assert.match(myItemsPageSource, /Мои предложения/);
  assert.doesNotMatch(mainSource, /Подать оффер/);
  assert.doesNotMatch(mainSource, /Мои предметы/);
});
