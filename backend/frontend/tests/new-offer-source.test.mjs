import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const pageSource = readFileSync(new URL("../src/pages/NewOfferPage.tsx", import.meta.url), "utf8");
const apiSource = readFileSync(new URL("../src/api/client.ts", import.meta.url), "utf8");

test("new offer form validates backend description minimum before submit", () => {
  assert.match(pageSource, /trimmedDescription\.length < 10/);
  assert.match(pageSource, /Описание должно быть не короче 10 символов/);
});

test("new offer form clamps too large declared value to 400000", () => {
  assert.match(pageSource, /const MAX_DECLARED_VALUE = 400000/);
  assert.match(pageSource, /function parseDeclaredValue/);
  assert.match(pageSource, /return MAX_DECLARED_VALUE/);
  assert.match(pageSource, /Math\.min\(Number\(normalized\), MAX_DECLARED_VALUE\)/);
});

test("new offer form has readable validation for all user fields", () => {
  assert.match(pageSource, /Название должно быть не короче 2 символов/);
  assert.match(pageSource, /Название должно быть не длиннее 255 символов/);
  assert.match(pageSource, /Название города должно быть не длиннее 100 символов/);
  assert.match(pageSource, /Имя участника должно быть не длиннее 255 символов/);
  assert.match(pageSource, /Оценка должна быть целым числом без букв и знаков/);
  assert.match(pageSource, /Для физического предмета нужно минимум одно фото/);
});

test("new offer form requires login and supports removing selected photos", () => {
  assert.match(pageSource, /getAdminToken/);
  assert.match(pageSource, /Чтобы предложить обмен, пожалуйста, зарегистрируйтесь/);
  assert.match(pageSource, /to="\/login"/);
  assert.match(pageSource, /to="\/register"/);
  assert.match(pageSource, /function removeFile/);
  assert.match(pageSource, /selected-photo-list/);
  assert.match(pageSource, /Удалить/);
});

test("new offer form sends optimized image metadata", () => {
  assert.match(apiSource, /thumbnail_url: string/);
  assert.match(apiSource, /thumbnail_width: number/);
  assert.match(pageSource, /photo_thumbnail_urls/);
  assert.match(pageSource, /photo_thumbnail_widths/);
  assert.match(pageSource, /photo_thumbnail_size_bytes/);
});

test("api client formats FastAPI validation errors", () => {
  assert.match(apiSource, /function formatValidationDetail/);
  assert.match(apiSource, /VALIDATION_FIELD_LABELS/);
  assert.match(apiSource, /function formatValidationMessage/);
  assert.match(apiSource, /Оценка слишком большая/);
  assert.match(apiSource, /record\.loc/);
  assert.match(apiSource, /record\.msg/);
  assert.match(apiSource, /validationMessage/);
});
