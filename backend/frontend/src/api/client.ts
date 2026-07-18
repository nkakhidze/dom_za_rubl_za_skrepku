const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "https://tomsk-dom-za-skrepku.space";

export type PublicOffer = {
  id: string;
  title: string;
  description: string;
  offer_type: string;
  city: string | null;
  public_value: number | null;
  public_comment: string | null;
  photo_urls: string[];
  thumbnail_urls: string[];
  participant_public_name: string | null;
  status_label: string;
  created_at: string;
};

export type PublicExchangeChainItem = {
  id: string;
  step_number: number;
  status: string;
  public_story: string | null;
  video_url: string | null;
  participant_public_name: string | null;
  participant_visible: boolean;
  deal_date: string | null;
  given_item: {
    id: string;
    title: string;
    description: string | null;
    public_story: string | null;
    photo_url: string | null;
    photo_urls: string[];
    thumbnail_url: string | null;
    thumbnail_urls: string[];
  };
  received_item: {
    id: string;
    title: string;
    description: string | null;
    public_story: string | null;
    photo_url: string | null;
    photo_urls: string[];
    thumbnail_url: string | null;
    thumbnail_urls: string[];
  };
};

export type PublicCurrentItem = {
  id: string;
  title: string;
  description: string | null;
  item_type: string;
  public_story: string | null;
  photo_url: string | null;
  thumbnail_urls: string[];
};

export type PublicItemDetail = {
  id: string;
  title: string;
  description: string | null;
  item_type: string;
  public_story: string | null;
  photo_url: string | null;
  photo_urls: string[];
  thumbnail_urls: string[];
  vk_url: string | null;
  tiktok_url: string | null;
  youtube_url: string | null;
  dzen_url: string | null;
  rutube_url: string | null;
  instagram_url: string | null;
};

export type CreateOfferPayload = {
  messenger_type: "web";
  external_user_id: string;
  username?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  title: string;
  description: string;
  offer_type: "physical_item" | "service";
  city: string;
  declared_value: number;
  photo_urls: string[];
  photo_thumbnail_urls?: Array<string | null>;
  photo_widths?: Array<number | null>;
  photo_heights?: Array<number | null>;
  photo_thumbnail_widths?: Array<number | null>;
  photo_thumbnail_heights?: Array<number | null>;
  photo_size_bytes?: Array<number | null>;
  photo_thumbnail_size_bytes?: Array<number | null>;
  exchange_preference: "any_offer" | "comparable_value_only";
  consent_accepted: boolean;
  participant_visible: boolean;
  participant_public_name?: string | null;
};

export type CreateOfferResponse = {
  id: string;
  status: string;
  message: string;
};

export type OfferLimitResponse = {
  status: "limit_reached";
  next_allowed_date: string | null;
  message: string;
};

export type CreateOfferResult = CreateOfferResponse | OfferLimitResponse;

export type ImageUploadResponse = {
  image_url: string;
  photo_url: string;
  thumbnail_url: string;
  filename: string;
  width: number;
  height: number;
  thumbnail_width: number;
  thumbnail_height: number;
  size_bytes: number;
  thumbnail_size_bytes: number;
  mime_type: string;
};

export type AdminOffer = {
  id: string;
  user_id: string;
  title: string;
  description: string;
  offer_type: string;
  city: string | null;
  declared_value: number | null;
  moderated_value: number | null;
  public_value: number | null;
  photo_urls: string[];
  thumbnail_urls: string[];
  exchange_preference: string;
  status: string;
  status_label: string;
  visibility_status: string;
  sort_priority: number;
  is_public: boolean;
  public_comment: string | null;
  participant_visible: boolean;
  participant_public_name: string | null;
  valuation_source: string | null;
  moderation_comment: string | null;
  created_at: string;
  updated_at: string;
  user_phone?: string | null;
  user_email?: string | null;
  telegram_phone?: string | null;
  telegram_username?: string | null;
  telegram_user_id?: string | null;
  consent_accepted?: boolean;
  consent_accepted_at?: string | null;
  consent_text_version?: string | null;
  requires_contract?: boolean;
  contract_status?: string;
  contract_file_key?: string | null;
};

export type AdminOfferPhoto = {
  id: string;
  offer_id: string;
  photo_url: string;
  thumbnail_url: string | null;
  width: number | null;
  height: number | null;
  thumbnail_width: number | null;
  thumbnail_height: number | null;
  size_bytes: number | null;
  thumbnail_size_bytes: number | null;
  created_at: string;
};

export type AdminItem = {
  id: string;
  user_id: string | null;
  source_offer_id: string | null;
  title: string;
  description: string | null;
  item_type: string;
  status: string;
  internal_value: number | null;
  valuation_source: string | null;
  owner_type: string;
  owner_name: string | null;
  is_current: boolean;
  is_public: boolean;
  sequence_number: number | null;
  public_story: string | null;
  photo_url: string | null;
  photo_urls: string[];
  thumbnail_urls: string[];
  photos: Array<{
    id: string;
    item_id: string;
    photo_url: string;
    thumbnail_url: string | null;
    width: number | null;
    height: number | null;
    thumbnail_width: number | null;
    thumbnail_height: number | null;
    size_bytes: number | null;
    thumbnail_size_bytes: number | null;
    sort_order: number;
    created_at: string;
  }>;
  vk_url: string | null;
  tiktok_url: string | null;
  youtube_url: string | null;
  dzen_url: string | null;
  rutube_url: string | null;
  instagram_url: string | null;
  created_at: string;
  updated_at: string;
};

export type AdminItemCreatePayload = {
  title: string;
  description?: string | null;
  item_type: "physical_item" | "service" | "money";
  internal_value?: number | null;
  valuation_source?: string | null;
  owner_type: "personal" | "tom_sawyer_fest" | "partner_org" | "other";
  owner_name?: string | null;
  is_current: boolean;
  is_public: boolean;
  public_story?: string | null;
  photo_url?: string | null;
  thumbnail_url?: string | null;
  width?: number | null;
  height?: number | null;
  thumbnail_width?: number | null;
  thumbnail_height?: number | null;
  size_bytes?: number | null;
  thumbnail_size_bytes?: number | null;
  vk_url?: string | null;
  tiktok_url?: string | null;
  youtube_url?: string | null;
  dzen_url?: string | null;
  rutube_url?: string | null;
  instagram_url?: string | null;
  sequence_number?: number | null;
};

export type AdminItemUpdatePayload = Partial<AdminItemCreatePayload> & {
  status?: string | null;
};

export type UserItem = {
  id: string;
  user_id: string;
  title: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type UserOffer = {
  id: string;
  title: string;
  description: string;
  offer_type: string;
  city: string | null;
  declared_value: number | null;
  status: string;
  status_label: string;
  is_public: boolean;
  public_comment: string | null;
  participant_visible: boolean;
  participant_public_name: string | null;
  photo_urls: string[];
  thumbnail_urls: string[];
  created_at: string;
};

export type CreateItemPayload = {
  user_id: string;
  title: string;
  description: string;
};

export type Deal = {
  id: string;
  offer_id: string;
  item_id: string;
  status: string;
  status_label: string;
  created_at: string;
};

export type UserDeal = {
  id: string;
  status: string;
  status_label: string;
  offer_id: string | null;
  offer_title: string | null;
  item_id: string;
  item_title: string;
  created_at: string;
};

export type AdminDealListItem = {
  deal_id: string;
  deal_status: string;
  deal_status_label: string;
  deal_created_at: string;
  offer_id: string | null;
  offer_title: string | null;
  offer_status: string | null;
  offer_is_public: boolean | null;
  offer_owner_user_id: string | null;
  offer_owner_display_name: string | null;
  item_id: string;
  item_title: string;
  item_status: string;
  item_owner_user_id: string | null;
  item_owner_display_name: string | null;
};

export type AdminDealUser = {
  id: string;
  display_name: string | null;
  phone: string | null;
  messenger_accounts: Array<{
    messenger_type: string;
    external_user_id: string;
    username: string | null;
    first_name: string | null;
    last_name: string | null;
  }>;
};

export type AdminDealDetail = {
  id: string;
  status: string;
  status_label: string;
  created_at: string;
  updated_at: string;
  offer: {
    id: string;
    title: string;
    description: string;
    city: string | null;
    public_value: number | null;
    status: string;
    is_public: boolean;
    photo_urls: string[];
  } | null;
  item: {
    id: string;
    title: string;
    description: string | null;
    status: string;
  };
  offer_owner: AdminDealUser | null;
  item_owner: AdminDealUser | null;
};

export type AdminDealResponse = {
  id: string;
  offer_id: string | null;
  step_number: number;
  given_item_id: string;
  received_item_id: string;
  item_id: string | null;
  status: string;
  status_label: string;
  participant_user_id: string | null;
  participant_public_name: string | null;
  participant_visible: boolean;
  public_story: string | null;
  video_url: string | null;
  is_public: boolean;
  deal_date: string;
  created_at: string;
  updated_at: string;
};

export type ModerationPayload = {
  moderated_value?: number | null;
  public_value?: number | null;
  valuation_source?: string | null;
  moderation_comment?: string | null;
  visibility_status?: "normal" | "low_priority" | "hidden";
  sort_priority?: number | null;
  is_public?: boolean;
  public_comment?: string | null;
  participant_visible?: boolean;
  participant_public_name?: string | null;
};

export type AuthUser = {
  id: string;
  display_name: string | null;
  login: string | null;
  phone: string | null;
  phone_verified: boolean;
  email: string | null;
  is_active: boolean;
  roles: string[];
};

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
  user: AuthUser;
};

export type LegalDocumentListItem = {
  code: string;
  title: string;
  version: string;
  effective_from: string;
  required: boolean;
  revocable: boolean;
  informational: boolean;
};

export type LegalDocumentDetail = LegalDocumentListItem & {
  content: string;
};

export type RegisterPayload = {
  login: string;
  password: string;
  password_confirmation: string;
  display_name: string;
  phone: string;
  email?: string | null;
  is_adult_confirmed: boolean;
  user_agreement: {
    accepted: boolean;
    version: string;
  };
  personal_data_consent: {
    accepted: boolean;
    version: string;
  };
  privacy_policy_version: string;
  marketing_consent: {
    version: string;
    email: boolean;
    telegram: boolean;
    max: boolean;
  };
};

export type UserConsent = {
  document_code: string;
  document_version: string;
  status: string;
  accepted_at: string | null;
  revoked_at: string | null;
  source: string;
  consent_payload: Record<string, unknown>;
};

export type AccountResponse = AuthUser & {
  created_at: string;
  consents: UserConsent[];
};

export type AccountUpdatePayload = {
  display_name: string;
  phone?: string | null;
  email?: string | null;
};

export type AccountPasswordUpdatePayload = {
  current_password: string;
  new_password: string;
  new_password_confirmation: string;
};

export type TelegramLinkStatus = {
  status: string;
  telegram_connected: boolean;
  telegram_username: string | null;
  deep_link: string | null;
};

export type TelegramLoginStartResponse = {
  request_id: string;
  status: "pending";
  deep_link: string | null;
  expires_at: string;
};

export type TelegramLoginStatusResponse = {
  status: "pending" | "authenticated" | "expired";
  access_token: string | null;
  token_type: "bearer";
  user: AuthUser | null;
};

const ADMIN_TOKEN_STORAGE_KEY = "paperclip_admin_token";

export function getAdminToken(): string {
  return window.localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY) || "";
}

export function setAdminToken(token: string) {
  window.localStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, token);
  window.dispatchEvent(new Event("paperclip-admin-token-changed"));
}

export function clearAdminToken() {
  window.localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
  window.dispatchEvent(new Event("paperclip-admin-token-changed"));
}

function adminHeaders() {
  const token = getAdminToken();

  if (!token) {
    throw new Error("Пожалуйста, зарегистрируйтесь");
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}

const VALIDATION_FIELD_LABELS: Record<string, string> = {
  city: "Город",
  consent_accepted: "Согласие",
  declared_value: "Оценка",
  description: "Описание",
  exchange_preference: "Предпочтение",
  external_user_id: "Пользователь",
  first_name: "Имя",
  last_name: "Фамилия",
  messenger_type: "Источник заявки",
  offer_type: "Тип",
  participant_public_name: "Имя участника",
  participant_visible: "Публичность участника",
  photo_urls: "Фото",
  title: "Название",
  username: "Username",
};

function formatValidationMessage(fieldName: string, message: string): string {
  if (fieldName === "declared_value") {
    if (message.includes("Unable to parse input string as an integer")) {
      return "Оценка слишком большая, поэтому сохраните её как 400000 ₽.";
    }

    if (message.includes("Input should be greater than or equal to 0")) {
      return "Оценка не может быть отрицательной.";
    }

    if (message.includes("Input should be a valid integer")) {
      return "Оценка должна быть целым числом.";
    }
  }

  if (message.includes("String should have at least")) {
    return `${VALIDATION_FIELD_LABELS[fieldName] || fieldName}: слишком короткое значение.`;
  }

  if (message.includes("String should have at most")) {
    return `${VALIDATION_FIELD_LABELS[fieldName] || fieldName}: слишком длинное значение.`;
  }

  if (message.includes("List should have at most 3 items")) {
    return "Можно загрузить не больше 3 фото.";
  }

  return `${VALIDATION_FIELD_LABELS[fieldName] || fieldName}: ${message}`;
}

function formatValidationDetail(detail: unknown): string | null {
  if (!Array.isArray(detail)) {
    return null;
  }

  const messages = detail
    .map((item) => {
      if (!item || typeof item !== "object") {
        return null;
      }

      const record = item as { loc?: unknown; msg?: unknown };
      const location = Array.isArray(record.loc)
        ? record.loc.filter((part) => part !== "body").join(".")
        : "";
      const fieldName = Array.isArray(record.loc)
        ? String(record.loc[record.loc.length - 1] || "")
        : "";
      const message = typeof record.msg === "string" ? record.msg : null;

      if (!message) {
        return null;
      }

      return formatValidationMessage(fieldName || location, message);
    })
    .filter(Boolean);

  return messages.length > 0 ? messages.join("; ") : null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    const responseCopy = response.clone();

    try {
      const payload = await response.json();

      if (response.status === 401) {
        message = "Пожалуйста, зарегистрируйтесь";
      } else if (response.status === 403) {
        message = "Недостаточно прав для этого действия";
      } else if (typeof payload.detail === "string") {
        message = payload.detail;
      } else {
        const validationMessage = formatValidationDetail(payload.detail);
        if (validationMessage) {
          message = validationMessage;
        } else if (typeof payload.message === "string") {
          message = payload.message;
        }
      }
    } catch {
      const text = await responseCopy.text();

      if (text) {
        message = text;
      }
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function getPublicOffers(): Promise<PublicOffer[]> {
  return request<PublicOffer[]>("/api/offers");
}

export function getPublicExchangeChain(): Promise<PublicExchangeChainItem[]> {
  return request<PublicExchangeChainItem[]>("/api/public/exchange-chain");
}

export function getPublicCurrentItem(): Promise<PublicCurrentItem> {
  return request<PublicCurrentItem>("/api/public/current-item");
}

export function getPublicItemById(itemId: string): Promise<PublicItemDetail> {
  return request<PublicItemDetail>(`/api/public/items/${itemId}`);
}

export function getPublicOfferById(offerId: string): Promise<PublicOffer> {
  return request<PublicOffer>(`/api/offers/${offerId}`);
}

export function uploadImage(file: File): Promise<ImageUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return request<ImageUploadResponse>("/api/files/images", {
    method: "POST",
    body: formData,
  });
}

export function createOffer(payload: CreateOfferPayload): Promise<CreateOfferResult> {
  const token = getAdminToken();

  return request<CreateOfferResult>("/api/offers", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
  });
}

export function loginAdmin(login: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>("/api/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ login, password }),
  });
}

export function loginUser(login: string, password: string): Promise<LoginResponse> {
  return loginAdmin(login, password);
}

export function registerUser(payload: RegisterPayload): Promise<LoginResponse> {
  return request<LoginResponse>("/api/auth/register", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function getMe(): Promise<AuthUser> {
  const token = getAdminToken();

  if (!token) {
    return Promise.reject(new Error("Пожалуйста, зарегистрируйтесь"));
  }

  return request<AuthUser>("/api/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export function getAccount(): Promise<AccountResponse> {
  return request<AccountResponse>("/api/auth/account", {
    headers: {
      Authorization: `Bearer ${getAdminToken()}`,
    },
  });
}

export function updateAccount(payload: AccountUpdatePayload): Promise<AccountResponse> {
  return request<AccountResponse>("/api/auth/account", {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${getAdminToken()}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function updateAccountPassword(payload: AccountPasswordUpdatePayload): Promise<{ status: string }> {
  return request<{ status: string }>("/api/auth/account/password", {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${getAdminToken()}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function getTelegramLinkStatus(): Promise<TelegramLinkStatus> {
  return request<TelegramLinkStatus>("/api/auth/account/telegram", {
    headers: {
      Authorization: `Bearer ${getAdminToken()}`,
    },
  });
}

export function createTelegramLink(): Promise<TelegramLinkStatus> {
  return request<TelegramLinkStatus>("/api/auth/account/telegram/link", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${getAdminToken()}`,
    },
  });
}

export function createTelegramLoginLink(): Promise<TelegramLoginStartResponse> {
  return request<TelegramLoginStartResponse>("/api/auth/telegram/login-link", {
    method: "POST",
  });
}

export function getTelegramLoginStatus(requestId: string): Promise<TelegramLoginStatusResponse> {
  return request<TelegramLoginStatusResponse>(`/api/auth/telegram/login-link/${requestId}`);
}

export function updateMarketingConsent(payload: {
  document_version: string;
  email: boolean;
  telegram: boolean;
  max: boolean;
}): Promise<UserConsent> {
  return request<UserConsent>("/api/auth/me/consents/marketing", {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${getAdminToken()}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function getLegalDocuments(): Promise<LegalDocumentListItem[]> {
  return request<LegalDocumentListItem[]>("/api/legal/documents");
}

export function getLegalDocument(documentCode: string): Promise<LegalDocumentDetail> {
  return request<LegalDocumentDetail>(`/api/legal/documents/${documentCode}`);
}

export function getLegalDocumentVersion(
  documentCode: string,
  version: string,
): Promise<LegalDocumentDetail> {
  return request<LegalDocumentDetail>(`/api/legal/documents/${documentCode}/versions/${version}`);
}

export function getAdminOffers(): Promise<AdminOffer[]> {
  return request<AdminOffer[]>("/api/admin/offers", {
    headers: adminHeaders(),
  });
}

export function getAdminOffersFiltered(params?: {
  offer_status?: string;
  visibility_status?: string | string[];
  sort?: string;
}): Promise<AdminOffer[]> {
  const searchParams = new URLSearchParams();

  if (params?.offer_status && params.offer_status !== "all") {
    searchParams.set("offer_status", params.offer_status);
  }

  if (Array.isArray(params?.visibility_status)) {
    params.visibility_status
      .filter((visibility) => visibility !== "all")
      .forEach((visibility) => searchParams.append("visibility_status", visibility));
  } else if (params?.visibility_status && params.visibility_status !== "all") {
    searchParams.set("visibility_status", params.visibility_status);
  }

  if (params?.sort) {
    searchParams.set("sort", params.sort);
  }

  const query = searchParams.toString();

  return request<AdminOffer[]>(`/api/admin/offers${query ? `?${query}` : ""}`, {
    headers: adminHeaders(),
  });
}

export function getAdminOfferById(offerId: string): Promise<AdminOffer> {
  return request<AdminOffer>(`/api/admin/offers/${offerId}`, {
    headers: adminHeaders(),
  });
}

export function getAdminOfferPhotos(offerId: string): Promise<AdminOfferPhoto[]> {
  return request<AdminOfferPhoto[]>(`/api/admin/offers/${offerId}/photos`, {
    headers: adminHeaders(),
  });
}

export function getAdminItems(params?: {
  is_current?: boolean;
  is_public?: boolean;
}): Promise<AdminItem[]> {
  const searchParams = new URLSearchParams();

  if (params?.is_current !== undefined) {
    searchParams.set("is_current", String(params.is_current));
  }

  if (params?.is_public !== undefined) {
    searchParams.set("is_public", String(params.is_public));
  }

  const query = searchParams.toString();

  return request<AdminItem[]>(`/api/admin/items${query ? `?${query}` : ""}`, {
    headers: adminHeaders(),
  });
}

export function createAdminItem(payload: AdminItemCreatePayload): Promise<AdminItem> {
  return request<AdminItem>("/api/admin/items", {
    method: "POST",
    headers: {
      ...adminHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function updateAdminItem(
  itemId: string,
  payload: AdminItemUpdatePayload,
): Promise<AdminItem> {
  return request<AdminItem>(`/api/admin/items/${itemId}`, {
    method: "PATCH",
    headers: {
      ...adminHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function addAdminItemPhoto(
  itemId: string,
  payload: {
    photo_url: string;
    thumbnail_url?: string | null;
    width?: number | null;
    height?: number | null;
    thumbnail_width?: number | null;
    thumbnail_height?: number | null;
    size_bytes?: number | null;
    thumbnail_size_bytes?: number | null;
    sort_order?: number;
  },
): Promise<AdminItem["photos"][number]> {
  return request<AdminItem["photos"][number]>(`/api/admin/items/${itemId}/photos`, {
    method: "POST",
    headers: {
      ...adminHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function deleteAdminItemPhoto(itemId: string, photoId: string): Promise<void> {
  return request<void>(`/api/admin/items/${itemId}/photos/${photoId}`, {
    method: "DELETE",
    headers: adminHeaders(),
  });
}

export function updateOfferModeration(
  offerId: string,
  payload: ModerationPayload,
): Promise<AdminOffer> {
  return request<AdminOffer>(`/api/admin/offers/${offerId}/moderation`, {
    method: "PATCH",
    headers: {
      ...adminHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function updateOfferStatus(offerId: string, status: string): Promise<AdminOffer> {
  return request<AdminOffer>(`/api/admin/offers/${offerId}/status`, {
    method: "PATCH",
    headers: {
      ...adminHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status }),
  });
}

export function createItem(payload: CreateItemPayload): Promise<UserItem> {
  return request<UserItem>("/api/items", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function getUserItems(userId: string): Promise<UserItem[]> {
  return request<UserItem[]>(`/api/users/${userId}/items`);
}

export function getMyOffers(): Promise<UserOffer[]> {
  return request<UserOffer[]>("/api/auth/me/offers", {
    headers: {
      Authorization: `Bearer ${getAdminToken()}`,
    },
  });
}

export function createDeal(payload: { offer_id: string; item_id: string }): Promise<Deal> {
  return request<Deal>("/api/deals", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function getUserDeals(userId: string): Promise<UserDeal[]> {
  return request<UserDeal[]>(`/api/users/${userId}/deals`);
}

export function getMyDeals(): Promise<UserDeal[]> {
  return request<UserDeal[]>("/api/auth/me/deals", {
    headers: {
      Authorization: `Bearer ${getAdminToken()}`,
    },
  });
}

export function getAdminDeals(): Promise<AdminDealListItem[]> {
  return request<AdminDealListItem[]>("/api/admin/deals", {
    headers: adminHeaders(),
  });
}

export function getAdminDealById(dealId: string): Promise<AdminDealDetail> {
  return request<AdminDealDetail>(`/api/admin/deals/${dealId}`, {
    headers: adminHeaders(),
  });
}

export function updateDealStatus(dealId: string, status: string): Promise<AdminDealDetail> {
  return request<AdminDealDetail>(`/api/admin/deals/${dealId}/status`, {
    method: "PATCH",
    headers: {
      ...adminHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status }),
  });
}

export function selectOfferAsNext(
  offerId: string,
  payload: {
    public_story?: string | null;
    video_url?: string | null;
    photo_url?: string | null;
    is_public: boolean;
  },
): Promise<AdminDealResponse> {
  return request<AdminDealResponse>(`/api/admin/offers/${offerId}/select-next`, {
    method: "POST",
    headers: {
      ...adminHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}
