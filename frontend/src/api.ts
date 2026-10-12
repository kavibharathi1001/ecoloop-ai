// const API_BASE_URL = (
//   import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:3000"
// ).replace(/\/+$/, "");
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "https://sn8ckghkt9.execute-api.ap-south-1.amazonaws.com"
).replace(/\/+$/, "");

export type Material =
  | "plastic"
  | "paper"
  | "glass"
  | "metal"
  | "organic"
  | "electronic"
  | "textile"
  | "unknown";

export type ActionType =
  | "reused"
  | "recycled"
  | "composted"
  | "donated"
  | "repaired"
  | "upcycled";

export interface ApiResponse {
  success?: boolean;
  message?: string;
  error?: string;
  [key: string]: unknown;
}

async function request<T extends ApiResponse>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });
  } catch {
    throw new Error(
      "Cannot connect to EcoLoop AI. Check that the backend is running.",
    );
  }

  const data = (await response.json().catch(() => ({}))) as T;

  if (!response.ok || data.success === false) {
    throw new Error(
      data.error || data.message || `API request failed (${response.status})`,
    );
  }

  return data;
}

function post<T extends ApiResponse>(
  path: string,
  body: unknown,
): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export const ecoLoopApi = {
  health: () => request<ApiResponse>("/health"),

  analyze: (item: string, material?: Material) =>
    post<ApiResponse>("/api/analyze", {
      item,
      ...(material ? { material } : {}),
    }),

  analyzeImage: (
    image: string,
    mimeType: string,
    description = "",
  ) =>
    post<ApiResponse>("/api/analyze-image", {
      image,
      mimeType,
      description,
    }),
  generateArtwork: (
    item: string,
    material: string,
    idea: string,
  ) =>
    post<ApiResponse>("/api/generate-artwork", {
      item,
      material,
      idea,
    }),

    
  chat: (message: string) =>
    post<ApiResponse>("/api/chat", { message }),

  recycling: () =>
    request<ApiResponse>("/api/recycling"),

  recordAction: (action: {
    sessionId: string;
    item: string;
    material: Material;
    actionType: ActionType;
    quantity: number;
  }) => post<ApiResponse>("/api/actions", action),

  getActions: (sessionId: string) =>
    request<ApiResponse>(
      `/api/actions?sessionId=${encodeURIComponent(sessionId)}`,
    ),

  getImpact: (sessionId: string) =>
    request<ApiResponse>(
      `/api/impact?sessionId=${encodeURIComponent(sessionId)}`,
    ),
};

export function getSessionId(): string {
  const storageKey = "ecoloop-session-id";

  try {
    const existing = localStorage.getItem(storageKey);

    if (existing) return existing;

    const created = `ecoloop-${crypto.randomUUID()}`;
    localStorage.setItem(storageKey, created);
    return created;
  } catch {
    return "ecoloop-session";
  }
}
