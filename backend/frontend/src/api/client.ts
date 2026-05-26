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
  created_at: string;
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
    throw new Error("Нужно указать корректный admin token");
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

      if (response.status === 401 || response.status === 403) {
        message = "Нужно указать корректный admin token";
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
