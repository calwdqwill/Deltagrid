import axios from "axios";
import { ApiResponse, DataSourceStatus } from "@/types/api";
import { ScannerListResponse, ScannerRecord } from "@/types/scanner";
import { ScannerPreferences, FavoritesResponse, PinnedResponse } from "@/types/preferences";
import { useAuthStore } from "@/stores/authStore";

const api = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
    "X-API-Version": "v1",
  },
});

// Auth interceptor: attach JWT when available
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth interceptor: handle 401 with token refresh
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status;

    if (status === 401 && originalRequest && !originalRequest._retry) {
      const refreshTokenValue = useAuthStore.getState().refreshToken;
      if (!refreshTokenValue) {
        useAuthStore.getState().logout();
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Wait for refresh to complete
        return new Promise((resolve) => {
          refreshSubscribers.push((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(api(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const res = await axios.post("/api/v1/auth/refresh", {
          refresh_token: refreshTokenValue,
        });
        const data = snakeToCamel(res.data?.data) as
          | { accessToken?: string; refreshToken?: string }
          | undefined;
        if (data?.accessToken) {
          useAuthStore.getState().setToken(data.accessToken);
          if (data.refreshToken) {
            useAuthStore.getState().setRefreshToken(data.refreshToken);
          }
          api.defaults.headers.common.Authorization = `Bearer ${data.accessToken}`;
          originalRequest.headers.Authorization = `Bearer ${data.accessToken}`;
          onRefreshed(data.accessToken);
          return api(originalRequest);
        }
      } catch (_e) {
        useAuthStore.getState().logout();
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export function snakeToCamel(obj: unknown): unknown {
  if (Array.isArray(obj)) return obj.map(snakeToCamel);
  if (obj === null || typeof obj !== "object") return obj;
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj)) {
    const camelKey = key.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase());
    result[camelKey] = snakeToCamel(value);
  }
  return result;
}

function camelToSnake(obj: unknown): unknown {
  if (Array.isArray(obj)) return obj.map(camelToSnake);
  if (obj === null || typeof obj !== "object") return obj;
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj)) {
    const snakeKey = key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
    result[snakeKey] = camelToSnake(value);
  }
  return result;
}

function transformResponse<T>(res: { data: ApiResponse<T> }): ApiResponse<T> {
  return {
    ...res.data,
    data: snakeToCamel(res.data.data) as T,
  };
}

// Scanner API
export async function fetchScanner(
  params?: Record<string, unknown>
): Promise<ApiResponse<ScannerListResponse>> {
  const res = await api.get("/scanner", { params });
  return transformResponse(res);
}

export async function fetchScannerDetail(id: string): Promise<ApiResponse<{ record: ScannerRecord }>> {
  const res = await api.get(`/scanner/${id}`);
  return transformResponse(res);
}

// Preferences API
export async function fetchPreferences(): Promise<ApiResponse<ScannerPreferences>> {
  const res = await api.get("/preferences");
  return transformResponse(res);
}

export async function updatePreferences(prefs: ScannerPreferences): Promise<ApiResponse<ScannerPreferences>> {
  const res = await api.post("/preferences", camelToSnake(prefs));
  return transformResponse(res);
}

export async function fetchFavorites(): Promise<ApiResponse<FavoritesResponse>> {
  const res = await api.get("/preferences/favorites");
  return transformResponse(res);
}

export async function toggleFavorite(instrumentId: string): Promise<ApiResponse<{ instrument_id: string; is_favorite: boolean }>> {
  const res = await api.post(`/preferences/favorites/${instrumentId}`);
  return transformResponse(res);
}

export async function fetchPinned(): Promise<ApiResponse<PinnedResponse>> {
  const res = await api.get("/preferences/pinned");
  return transformResponse(res);
}

export async function togglePinned(instrumentId: string): Promise<ApiResponse<{ instrument_id: string; is_pinned: boolean }>> {
  const res = await api.post(`/preferences/pinned/${instrumentId}`);
  return transformResponse(res);
}

// Auth API
export async function login(credentials: { email: string; password: string }): Promise<ApiResponse<{ accessToken: string; refreshToken: string; tokenType: string; user: { id: string; email: string | null; username: string | null; plan: string } }>> {
  const res = await api.post("/auth/login", credentials);
  return transformResponse(res);
}

export async function register(credentials: { email: string; password: string; username?: string }): Promise<ApiResponse<{ accessToken: string; refreshToken: string; tokenType: string; user: { id: string; email: string | null; username: string | null; plan: string } }>> {
  const res = await api.post("/auth/register", credentials);
  return transformResponse(res);
}

export async function refreshToken(refreshToken: string): Promise<ApiResponse<{ accessToken: string; refreshToken: string; tokenType: string; user: { id: string; email: string | null; username: string | null; plan: string } }>> {
  const res = await api.post("/auth/refresh", { refresh_token: refreshToken });
  return transformResponse(res);
}

export async function fetchMe(): Promise<ApiResponse<{ id: string; email: string | null; username: string | null; plan: string }>> {
  const res = await api.get("/auth/me");
  return transformResponse(res);
}

// Paper Trading API
export async function fetchPaperAccounts(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/paper/accounts");
  return transformResponse(res);
}

export async function createPaperAccount(data: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.post("/paper/accounts", camelToSnake(data));
  return transformResponse(res);
}

export async function fetchPaperTrades(accountId: string): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get(`/paper/accounts/${accountId}/trades`);
  return transformResponse(res);
}

export async function createPaperTrade(accountId: string, data: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.post(`/paper/accounts/${accountId}/trades`, camelToSnake(data));
  return transformResponse(res);
}

export async function closePaperTrade(accountId: string, tradeId: string, exitPrice: number): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.post(`/paper/accounts/${accountId}/trades/${tradeId}/close?exit_price=${exitPrice}`);
  return transformResponse(res);
}

export async function fetchPortfolio(accountId: string): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.get(`/paper/accounts/${accountId}/portfolio`);
  return transformResponse(res);
}

// Performance API
export async function fetchPerformanceMetrics(accountId: string): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.get(`/performance/accounts/${accountId}`);
  return transformResponse(res);
}

// Billing API
export async function fetchPlans(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/billing/plans");
  return transformResponse(res);
}

// Health API
export async function fetchHealth(): Promise<ApiResponse<{ status: string; version: string; timestamp: string }>> {
  const res = await api.get("/health");
  return transformResponse(res);
}

export async function fetchStatus(): Promise<ApiResponse<{ sources: DataSourceStatus[]; cache: Record<string, unknown>; timestamp: string }>> {
  const res = await api.get("/health/status");
  return transformResponse(res);
}

// Market API
export async function fetchTrending(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/market/trending");
  return transformResponse(res);
}

export async function fetchGainers(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/market/gainers");
  return transformResponse(res);
}

export async function fetchLosers(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/market/losers");
  return transformResponse(res);
}

export async function fetchGlobal(): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.get("/market/global");
  return transformResponse(res);
}

export async function fetchFearGreed(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/market/fear-greed");
  return transformResponse(res);
}

export async function fetchNewListings(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/market/new-listings");
  return transformResponse(res);
}

export async function fetchFundingRates(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/market/funding-rates");
  return transformResponse(res);
}

// Exchange Accounts API
export async function fetchExchangeAccounts(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/exchange-accounts");
  return transformResponse(res);
}

export async function createExchangeAccount(data: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.post("/exchange-accounts", camelToSnake(data));
  return transformResponse(res);
}

export async function deleteExchangeAccount(id: string): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.delete(`/exchange-accounts/${id}`);
  return transformResponse(res);
}

export async function storeExchangeKeys(accountId: string, data: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.post(`/exchange-accounts/${accountId}/keys`, camelToSnake(data));
  return transformResponse(res);
}

export async function fetchConnectors(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/exchange-accounts/connectors/capabilities");
  return transformResponse(res);
}

// Execution API
export async function createOrderIntent(data: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.post("/execution/intents", camelToSnake(data));
  return transformResponse(res);
}

export async function fetchOrderIntents(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/execution/intents");
  return transformResponse(res);
}

export async function confirmOrderIntent(id: string, isLive: boolean = false): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.post(`/execution/intents/${id}/confirm?is_live=${isLive}`);
  return transformResponse(res);
}

export async function cancelOrderIntent(id: string): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.delete(`/execution/intents/${id}`);
  return transformResponse(res);
}

export async function fetchOrders(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/execution/orders");
  return transformResponse(res);
}

export async function fetchOrderEvents(orderId: string): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get(`/execution/orders/${orderId}/events`);
  return transformResponse(res);
}

// Risk API
export async function fetchRiskRules(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/risk/rules");
  return transformResponse(res);
}

export async function createRiskRule(data: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.post("/risk/rules", camelToSnake(data));
  return transformResponse(res);
}

export async function deleteRiskRule(id: string): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.delete(`/risk/rules/${id}`);
  return transformResponse(res);
}

export async function dryRunRiskCheck(data: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.post("/risk/check", camelToSnake(data));
  return transformResponse(res);
}

export async function toggleRiskRule(id: string): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.post(`/risk/rules/${id}/toggle`);
  return transformResponse(res);
}

// Execution Sessions API
export async function fetchExecutionSessions(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/execution/sessions");
  return transformResponse(res);
}

export async function startExecutionSession(data: Record<string, unknown>): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.post("/execution/sessions", camelToSnake(data));
  return transformResponse(res);
}

export async function stopExecutionSession(id: string): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.post(`/execution/sessions/${id}/stop`);
  return transformResponse(res);
}

// RWA API
export async function fetchRwaAssets(category?: string): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/rwa/assets", { params: category ? { category } : undefined });
  return transformResponse(res);
}

export async function fetchRwaAsset(id: string): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.get(`/rwa/assets/${id}`);
  return transformResponse(res);
}

export async function fetchRwaCategories(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/rwa/categories");
  return transformResponse(res);
}

export async function compareRwaAssets(a: string, b: string): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.get("/rwa/compare", { params: { a, b } });
  return transformResponse(res);
}

// Treasury API
export async function fetchTreasuryEntities(entityType?: string): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/treasury/entities", { params: entityType ? { entity_type: entityType } : undefined });
  return transformResponse(res);
}

export async function fetchTreasuryEntity(id: string): Promise<ApiResponse<Record<string, unknown>>> {
  const res = await api.get(`/treasury/entities/${id}`);
  return transformResponse(res);
}

export async function fetchBtcHoldings(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/treasury/btc-holdings");
  return transformResponse(res);
}

export async function fetchTokenizationPlatforms(): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await api.get("/treasury/platforms");
  return transformResponse(res);
}

export default api;
