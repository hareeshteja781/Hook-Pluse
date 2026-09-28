export const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function formatApiError(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map(item => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) return String((item as { msg: unknown }).msg);
        return JSON.stringify(item);
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") {
    if ("msg" in detail) return String((detail as { msg: unknown }).msg);
    return JSON.stringify(detail);
  }
  return fallback;
}

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(formatApiError(body.detail, `Request failed (${response.status})`));
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

export type Endpoint = { id: string; name: string; target_url: string; is_active: boolean; created_at: string };
export type Dashboard = {
  endpoints: { total: number; active: number };
  events: Record<string, number> & { total: number };
  recent_events: { id: string; endpoint_id: string; event_type: string; status: string; received_at: string }[];
};

export async function healthCheck() {
  return parse<{ status: string; service: string }>(await fetch(`${API}/health`));
}

export async function getMe(token: string) {
  return parse<{ id: string; email: string; is_active: boolean }>(
    await fetch(`${API}/api/v1/auth/me`, { headers: authHeaders(token) }),
  );
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams({ username: email, password });
  return parse<{ access_token: string; token_type: string }>(
    await fetch(`${API}/api/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body }),
  );
}

export async function register(email: string, password: string) {
  return parse(await fetch(`${API}/api/v1/auth/register`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) }));
}

function authHeaders(token: string) { return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }; }

export async function getDashboard(token: string) {
  return parse<Dashboard>(await fetch(`${API}/api/v1/dashboard/summary`, { headers: authHeaders(token) }));
}

export async function getEndpoints(token: string) {
  return parse<Endpoint[]>(await fetch(`${API}/api/v1/endpoints`, { headers: authHeaders(token) }));
}

export async function createEndpoint(token: string, name: string, target_url: string) {
  return parse<Endpoint & { signing_secret: string }>(await fetch(`${API}/api/v1/endpoints`, { method: "POST", headers: authHeaders(token), body: JSON.stringify({ name, target_url }) }));
}

export async function deleteEndpoint(token: string, id: string) {
  await parse<void>(await fetch(`${API}/api/v1/endpoints/${id}`, { method: "DELETE", headers: authHeaders(token) }));
}

export function websocketUrl() {
  const url = new URL(API);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `${url.pathname.replace(/\/$/, "")}/api/v1/ws/events`;
  return url.toString();
}

export type EventAttempt = { id: string; attempt_number: number; http_status: number | null; duration_ms: number | null; response_body: string | null; error: string | null; created_at: string };
export type EventDetail = {
  id: string; endpoint_id: string; idempotency_key: string; body_hash: string;
  payload: Record<string, unknown>; headers: Record<string, unknown>; signature: string;
  event_type: string | null; status: string; next_retry_at: string | null; replay_of_id: string | null;
  received_at: string; attempts: EventAttempt[];
};

export async function getEvent(token: string, id: string) {
  return parse<EventDetail>(await fetch(`${API}/api/v1/events/${id}`, { headers: authHeaders(token) }));
}

export async function replayEvent(token: string, id: string) {
  return parse<{ event_id: string; replay_of_id: string; status: string }>(
    await fetch(`${API}/api/v1/events/${id}/replay`, { method: "POST", headers: authHeaders(token) }),
  );
}

export type Metrics = {
  events: { total: number; delivered: number; failed: number; dlq: number };
  delivery: { attempts: number; successful_attempts: number; success_rate: number; avg_latency_ms: number };
};

export async function getMetrics(token: string) {
  return parse<Metrics>(await fetch(`${API}/api/v1/metrics/summary`, { headers: authHeaders(token) }));
}

export async function sendSimulator(token: string, endpoint_id: string, count: number, event_type: string) {
  return parse<{ created: number; dispatched: number }>(
    await fetch(`${API}/api/v1/simulator/send`, { method: "POST", headers: authHeaders(token), body: JSON.stringify({ endpoint_id, count, event_type }) }),
  );
}
