/**
 * Backend API client.
 * Base URL comes from NEXT_PUBLIC_API_URL so the frontend stays decoupled from
 * the FastAPI service. Local development may omit the variable and talk to
 * localhost. Production must set NEXT_PUBLIC_API_URL to the public API;
 * missing it yields an empty base so the UI does not call the author's machine.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  (process.env.NODE_ENV === "production" ? "" : "http://localhost:8000/api/v1");

export const isApiConfigured = Boolean(API_BASE_URL);

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface GetOptions {
  params?: Record<string, string | number | boolean | null | undefined>;
  signal?: AbortSignal;
}

export function buildQuery(params: GetOptions["params"]): string {
  if (!params) return "";
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  });
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

/** List pages may emit nextCursor (wire) or next_cursor (raw dict). */
export function readNextCursor(payload: {
  nextCursor?: string | null;
  next_cursor?: string | null;
}): string | null {
  const value = payload.nextCursor ?? payload.next_cursor;
  return value ? value : null;
}

export async function apiGet<T>(path: string, options: GetOptions = {}): Promise<T> {
  if (!isApiConfigured) {
    throw new ApiError("API base URL is not configured.", 0);
  }

  const url = `${API_BASE_URL}${path}${buildQuery(options.params)}`;
  const response = await fetch(url, {
    method: "GET",
    headers: {
      Accept: "application/json",
      // Bypasses the ngrok interstitial page, which would otherwise replace the
      // JSON payload with HTML when the API is reached through a tunnel.
      "ngrok-skip-browser-warning": "1",
    },
    signal: options.signal,
  });

  if (!response.ok) {
    throw new ApiError(`Request failed: ${response.statusText}`, response.status);
  }

  return (await response.json()) as T;
}
