import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const pageSource = readFileSync(new URL("../src/pages/OffersPage.tsx", import.meta.url), "utf8");
const itemPageSource = readFileSync(new URL("../src/pages/PublicItemPage.tsx", import.meta.url), "utf8");
const apiSource = readFileSync(new URL("../src/api/client.ts", import.meta.url), "utf8");

test("exchange history page uses public deals endpoint instead of public offers", () => {
  assert.match(pageSource, /getPublicExchangeChain/);
  assert.match(pageSource, /getPublicCurrentItem/);
  assert.doesNotMatch(pageSource, /getPublicOffers/);
  assert.match(apiSource, /\/api\/public\/exchange-chain/);
  assert.match(apiSource, /\/api\/public\/current-item/);
});

test("exchange history page renders a linked item chain instead of step cards", () => {
  assert.match(pageSource, /buildChainNodes/);
  assert.match(pageSource, /buildChainNodes\(deals, currentItem\)\.reverse\(\)/);
  assert.match(pageSource, /currentItemToChainItem/);
  assert.doesNotMatch(pageSource, /Старт/);
  assert.doesNotMatch(pageSource, /Получили/);
  assert.doesNotMatch(pageSource, /chain-label/);
  assert.doesNotMatch(pageSource, /Шаг №/);
  assert.doesNotMatch(pageSource, /Отдали/);
});

test("exchange history page removes old offer copy and offer detail links", () => {
  assert.doesNotMatch(pageSource, /Опубликованные предложения для цепочки обменов/);
  assert.doesNotMatch(pageSource, /\/offers\/\$\{/);
});

test("exchange history page handles empty state and missing photos", () => {
  assert.match(pageSource, /История обменов пока не опубликована/);
  assert.match(pageSource, /Нет фото/);
});

test("exchange history items open public item detail pages", () => {
  assert.match(pageSource, /\/items\/\$\{node\.item\.id\}/);
  assert.match(pageSource, /className="thumb-link"/);
  assert.match(pageSource, /thumbnail_urls\[0\]/);
  assert.match(pageSource, /thumbnail_url/);
  assert.match(apiSource, /\/api\/public\/items\/\$\{itemId\}/);
  assert.match(itemPageSource, /fullscreen-gallery/);
  assert.match(itemPageSource, /event\.key === "Escape"/);
  assert.match(itemPageSource, /showNextPhotoOrClose/);
  assert.match(itemPageSource, /current >= photos\.length - 1 \? null : current \+ 1/);
  assert.match(itemPageSource, /PLATFORM_LINKS/);
  assert.match(itemPageSource, /public_story/);
});
