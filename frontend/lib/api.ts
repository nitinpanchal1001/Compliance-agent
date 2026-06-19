// Thin fetch client for the compliance API. Attaches the JWT, transparently
// refreshes an expired access token once, and surfaces clean error messages.

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const ACCESS_KEY = "ca_access";
const REFRESH_KEY = "ca_refresh";

export const tokenStore = {
  get access() {
    return typeof window === "undefined" ? null : localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return typeof window === "undefined" ? null : localStorage.getItem(REFRESH_KEY);
  },
  set(access: string, refresh?: string) {
    localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((d: { msg?: string }) => d.msg ?? "invalid").join("; ");
    }
    return res.statusText;
  } catch {
    return res.statusText || `HTTP ${res.status}`;
  }
}

async function tryRefresh(): Promise<boolean> {
  const refresh = tokenStore.refresh;
  if (!refresh) return false;
  const res = await fetch(`${BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!res.ok) return false;
  const data = await res.json();
  // Refresh tokens rotate server-side — persist the new pair.
  tokenStore.set(data.access_token, data.refresh_token);
  return true;
}

interface Opts {
  method?: string;
  body?: unknown;
  auth?: boolean;
  isForm?: boolean;
  _retried?: boolean;
}

export async function api<T>(path: string, opts: Opts = {}): Promise<T> {
  const { method = "GET", body, auth = true, isForm = false } = opts;
  const headers: Record<string, string> = {};
  if (auth && tokenStore.access) headers.Authorization = `Bearer ${tokenStore.access}`;
  if (body !== undefined && !isForm) headers["Content-Type"] = "application/json";

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: isForm ? (body as BodyInit) : body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && auth && !opts._retried) {
    if (await tryRefresh()) {
      return api<T>(path, { ...opts, _retried: true });
    }
  }
  if (!res.ok) {
    throw new ApiError(await parseError(res), res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}
