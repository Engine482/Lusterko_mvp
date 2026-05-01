import { API_BASE_URL } from "@/lib/env";
import type { ApiError, ApiResponse } from "@/types/api";

export class ApiCallError extends Error {
  readonly code: ApiError["error"]["code"];
  readonly status: number;
  readonly details?: Record<string, unknown>;

  constructor(payload: ApiError, status: number) {
    super(payload.error.message);
    this.code = payload.error.code;
    this.status = status;
    this.details = payload.error.details;
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
};

export async function apiCall<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, signal } = options;
  const url = `${API_BASE_URL}${path}`;
  const init: RequestInit = {
    method,
    credentials: "include",
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal,
  };

  const res = await fetch(url, init);
  const payload = (await res.json()) as ApiResponse<T>;

  if (payload.success) {
    return payload.data;
  }
  throw new ApiCallError(payload, res.status);
}
