import { ApiResponse } from "@/types/api";

const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";
const DEFAULT_FETCH_TIMEOUT_MS = 5000;

function apiBaseUrl() {
  const configuredUrl = process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || DEFAULT_BACKEND_URL;
  const normalizedUrl = configuredUrl.replace(/\/$/, "");

  return normalizedUrl.endsWith("/api/v1") ? normalizedUrl : `${normalizedUrl}/api/v1`;
}

function fetchTimeoutMs() {
  const parsed = Number.parseInt(process.env.BACKEND_FETCH_TIMEOUT_MS ?? "", 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_FETCH_TIMEOUT_MS;
}

export async function fetchServerApi<T>(path: string): Promise<ApiResponse<T> | null> {
  const requestPath = path.startsWith("/") ? path : `/${path}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), fetchTimeoutMs());

  try {
    const response = await fetch(`${apiBaseUrl()}${requestPath}`, {
      cache: "no-store",
      headers: {
        "User-Agent": "DeltaGridFrontend/1.0",
      },
      signal: controller.signal,
    });
    if (!response.ok) return null;

    return (await response.json()) as ApiResponse<T>;
  } catch {
    return null;
  } finally {
    clearTimeout(timeout);
  }
}
