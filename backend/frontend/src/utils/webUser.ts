const STORAGE_KEY = "paperclip_web_external_user_id";

export function getWebExternalUserId(): string {
  const existing = window.localStorage.getItem(STORAGE_KEY);

  if (existing) {
    return existing;
  }

  const id = `web-${crypto.randomUUID()}`;
  window.localStorage.setItem(STORAGE_KEY, id);

  return id;
}
