const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

export type PublicOffer = {
  id: string;
  title: string;
  description: string;
  offer_type: string;
  city: string | null;
  public_value: number | null;
  public_comment: string | null;
  photo_urls: string[];
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
    photo_url: string | null;
  };
  received_item: {
    id: string;
    title: string;
    description: string | null;
    photo_url: string | null;
  };
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
  photo_url: string;
  filename: string;
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
  exchange_preference: string;
  status: string;
  status_label: string;
  is_public: boolean;
  public_comment: string | null;
  participant_visible: boolean;
  participant_public_name: string | null;
  valuation_source: string | null;
  moderation_comment: string | null;
  created_at: string;
  updated_at: string;
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
  created_at: string;
};

export type AdminItem = {
  id: string;
  user_id: string | null;
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
  public_story: string | null;
  photo_url: string | null;
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

export type CreateDealFromOfferPayload = {
  given_item_id: string;
  owner_type: "personal" | "tom_sawyer_fest" | "partner_org" | "other";
  owner_name?: string | null;
  public_story?: string | null;
  video_url?: string | null;
  photo_url?: string | null;
  is_public: boolean;
};

export type ModerationPayload = {
  moderated_value?: number | null;
  public_value?: number | null;
  valuation_source?: string | null;
  moderation_comment?: string | null;
  is_public?: boolean;
  public_comment?: string | null;
  participant_visible?: boolean;
  participant_public_name?: string | null;
};

export type AuthUser = {
  id: string;
  display_name: string | null;
  login: string | null;
  is_active: boolean;
  roles: string[];
};

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
  user: AuthUser;
};

const ADMIN_TOKEN_STORAGE_KEY = "paperclip_admin_token";

export function getAdminToken(): string {
  return window.localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY) || "";
}

export function setAdminToken(token: string) {
  window.localStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, token);
}

export function clearAdminToken() {
  window.localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
}

function adminHeaders() {
  const token = getAdminToken();

  if (!token) {
    throw new Error("Нужно войти в админку");
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    const responseCopy = response.clone();

    try {
      const payload = await response.json();

      if (response.status === 401) {
        message = "Нужно войти в админку";
      } else if (response.status === 403) {
        message = "Недостаточно прав для этого действия";
      } else if (typeof payload.detail === "string") {
        message = payload.detail;
      } else if (typeof payload.message === "string") {
        message = payload.message;
      }
    } catch {
      const text = await responseCopy.text();

      if (text) {
        message = text;
      }
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export function getPublicOffers(): Promise<PublicOffer[]> {
  return request<PublicOffer[]>("/api/offers");
}

export function getPublicExchangeChain(): Promise<PublicExchangeChainItem[]> {
  return request<PublicExchangeChainItem[]>("/api/public/exchange-chain");
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
  return request<CreateOfferResult>("/api/offers", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
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

export function getMe(): Promise<AuthUser> {
  return request<AuthUser>("/api/auth/me", {
    headers: adminHeaders(),
  });
}

export function getAdminOffers(): Promise<AdminOffer[]> {
  return request<AdminOffer[]>("/api/admin/offers", {
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

export function createDealFromOffer(
  offerId: string,
  payload: CreateDealFromOfferPayload,
): Promise<AdminDealResponse> {
  return request<AdminDealResponse>(`/api/admin/deals/from-offer/${offerId}`, {
    method: "POST",
    headers: {
      ...adminHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}
