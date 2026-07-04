import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const routerSource = readFileSync(
  new URL("../../app/api/routers/admin_offers.py", import.meta.url),
  "utf8",
);
const itemsRouterSource = readFileSync(
  new URL("../../app/api/routers/admin_items.py", import.meta.url),
  "utf8",
);
const itemSchemaSource = readFileSync(
  new URL("../../app/schemas/item.py", import.meta.url),
  "utf8",
);

test("admin offers backend excludes selected offers by default", () => {
  assert.match(routerSource, /Offer\.status != OfferStatus\.SELECTED\.value/);
  assert.match(routerSource, /if offer_status is not None/);
});

test("admin offers backend sorts admin-valued offers before user-valued offers", () => {
  assert.match(routerSource, /sort: str = Query\(default="value_desc"/);
  assert.match(routerSource, /admin_value_presence_sort/);
  assert.match(routerSource, /Offer\.moderated_value\.is_not\(None\)/);
  assert.match(routerSource, /admin_value_presence_sort\.desc\(\)/);
  assert.match(routerSource, /Offer\.moderated_value\.desc\(\)\.nullslast\(\)/);
  assert.match(routerSource, /Offer\.declared_value\.desc\(\)\.nullslast\(\)/);
  assert.match(routerSource, /Offer\.created_at\.desc\(\)/);
});

test("admin items backend supports editing chain items", () => {
  assert.match(itemsRouterSource, /@router\.patch\("\/{item_id}"/);
  assert.match(itemsRouterSource, /AdminItemUpdateRequest/);
  assert.match(itemsRouterSource, /db\.get\(Item, item_id\)/);
  assert.match(itemsRouterSource, /db\.commit\(\)/);
});

test("admin items backend sorts current and newest exchange items first", () => {
  assert.match(itemsRouterSource, /Item\.is_current\.desc\(\)/);
  assert.match(itemsRouterSource, /received_deal_date\.desc\(\)\.nullslast\(\)/);
  assert.match(itemsRouterSource, /Item\.sequence_number\.desc\(\)\.nullslast\(\)/);
});

test("admin and super admin can add and delete item photos", () => {
  assert.match(itemsRouterSource, /\/\{item_id\}\/photos/);
  assert.match(itemsRouterSource, /RoleCode\.ADMIN\.value, RoleCode\.SUPER_ADMIN\.value/);
  assert.match(itemsRouterSource, /ItemPhoto/);
  assert.match(itemSchemaSource, /AdminItemPhotoCreateRequest/);
  assert.match(itemSchemaSource, /AdminItemPhotoResponse/);
});
