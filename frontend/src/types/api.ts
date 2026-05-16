export interface ApiResponse<T> {
  success: boolean;
  data: T;
  meta: Record<string, unknown>;
}

export interface DataSourceStatus {
  source: string;
  status: string;
  lastSuccess?: string;
  lastError?: string;
  recordsFetched: number;
  latencyMs?: number;
}
