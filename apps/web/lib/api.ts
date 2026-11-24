// Backend adresi tek yerde durur. NEXT_PUBLIC_ önekli değişkenler tarayıcıya gömülür,
// bu yüzden buraya asla secret/parola koyma.
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const API = `${API_BASE_URL}/api/v1`;

export type HealthResponse = {
  status: string;
  service: string;
};

export type Collection = {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
};

export type DocumentStatus = "pending" | "processing" | "ready" | "failed";

export type DocumentItem = {
  id: string;
  collection_id: string;
  filename: string;
  mime_type: string;
  file_size: number;
  checksum: string;
  status: DocumentStatus;
  error_message: string | null;
  page_count: number | null;
  created_at: string;
};

/** Backend'in döndürdüğü hatayı kullanıcıya gösterilecek bir mesaja çevirir. */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API}${path}`, { cache: "no-store", ...init });
  } catch {
    // fetch yalnızca ağ hatasında (sunucu kapalı, CORS engeli...) fırlatır.
    throw new ApiError(0, "Sunucuya ulaşılamadı.");
  }

  if (!response.ok) {
    let message = `Beklenmeyen hata (${response.status}).`;
    try {
      const body = await response.json();
      // 400/404/409/413: { detail: "metin" }.  422 (doğrulama): detail bir LİSTEDİR.
      if (typeof body.detail === "string") message = body.detail;
      else if (response.status === 422) message = "Gönderilen bilgi geçersiz.";
    } catch {
      /* gövde JSON değil: varsayılan mesaj kalsın */
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) return undefined as T; // gövde yok (silme)
  return response.json();
}

export const fetchHealth = () => request<HealthResponse>("/health");

export const fetchCollections = () => request<Collection[]>("/collections");

export const createCollection = (name: string) =>
  request<Collection>("/collections", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });

export const fetchDocuments = (collectionId: string) =>
  request<DocumentItem[]>(
    `/documents?collection_id=${encodeURIComponent(collectionId)}`,
  );

export function uploadDocument(collectionId: string, file: File) {
  // FormData'yı biz doldururuz; Content-Type'ı TARAYICI ayarlar
  // (sınır dizesi "boundary" ile birlikte). Elle yazarsak bozulur.
  const form = new FormData();
  form.append("collection_id", collectionId);
  form.append("file", file);
  return request<DocumentItem>("/documents/upload", {
    method: "POST",
    body: form,
  });
}

export const deleteDocument = (documentId: string) =>
  request<void>(`/documents/${encodeURIComponent(documentId)}`, {
    method: "DELETE",
  });
