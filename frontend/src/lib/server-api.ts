import { ApiResponse } from "@/types/api";

const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

function apiBaseUrl() {
  const configuredUrl = process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || DEFAULT_BACKEND_URL;
  const normalizedUrl = configuredUrl.replace(/\/$/, "");

  return normalizedUrl.endsWith("/api/v1") ? normalizedUrl : `${normalizedUrl}/api/v1`;
}

export async function fetchServerApi<T>(path: string): Promise<ApiResponse<T> | null> {
  const requestPath = path.startsWith("/") ? path : `/${path}`;

  try {
    const response = await fetch(`${apiBaseUrl()}${requestPath}`, { cache: "no-store" });
    if (!response.ok) return null;

    return (await response.json()) as ApiResponse<T>;
  } catch {
    return null;
  }
}
