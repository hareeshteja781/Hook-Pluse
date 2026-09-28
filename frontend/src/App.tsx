import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { createEndpoint, deleteEndpoint, getDashboard, getEndpoints, login, register, websocketUrl } from "./api";
import type { Dashboard, Endpoint } from "./api";
import EventInspector from "./EventInspector";
import MetricsPanel from "./MetricsPanel";
import ApiTestPanel from "./ApiTestPanel";

const tokenKey = "hookpluse_token";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem(tokenKey));
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState("");

  if (!token) {
    return <Auth mode={mode} email={email} password={password} setEmail={setEmail} setPassword={setPassword} setMode={setMode} setToken={setToken} setError={setError} error={error} />;
  }
  return <DashboardView token={token} onLogout={() => { localStorage.removeItem(tokenKey); setToken(null); }} />;
}

type AuthProps = {
  mode: "login" | "register"; email: string; password: string; error: string;
  setEmail: (v: string) => void; setPassword: (v: string) => void; setMode: (v: "login" | "register") => void;
  setToken: (v: string) => void; setError: (v: string) => void;
};

function Auth(p: AuthProps) {
  const [testBusy, setTestBusy] = useState(false);
  const testLoginEnabled = import.meta.env.DEV || import.meta.env.VITE_ENABLE_TEST_LOGIN === "true";

  async function submit(e: FormEvent) {
    e.preventDefault(); p.setError("");
    try {
      if (p.mode === "register") await register(p.email, p.password);
      const result = await login(p.email, p.password);
      localStorage.setItem(tokenKey, result.access_token); p.setToken(result.access_token);
    } catch (err) { p.setError(err instanceof Error ? err.message : "Unable to authenticate"); }
  }

  async function testLogin() {
    setTestBusy(true); p.setError("");
    const testEmail = "test@hookpluse.com";
    const testPassword = "HookPluseTest123!";
    try {
      let result;
      try {
        result = await login(testEmail, testPassword);
      } catch {
        await register(testEmail, testPassword);
        result = await login(testEmail, testPassword);
      }
      localStorage.setItem(tokenKey, result.access_token);
      p.setToken(result.access_token);
    } catch (err) {
      p.setError(err instanceof Error ? err.message : "Test login failed");
    } finally {
      setTestBusy(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="brand-mark">HP</div>
        <p className="eyebrow">HOOK PLUSE</p>
        <h1>{p.mode === "login" ? "Sign in to your gateway" : "Create your workspace"}</h1>
        <p className="muted">Manage delivery endpoints, events, retries, and replay from one dashboard.</p>
        <form onSubmit={submit} className="stack">
          <label>Email<input type="email" value={p.email} onChange={e => p.setEmail(e.target.value)} required /></label>
          <label>Password<input type="password" minLength={8} value={p.password} onChange={e => p.setPassword(e.target.value)} required /></label>
          {p.error && <div className="alert">{p.error}</div>}
          <button className="primary" type="submit">{p.mode === "login" ? "Sign in" : "Create account"}</button>
        </form>
        <button className="link-button" onClick={() => { p.setMode(p.mode === "login" ? "register" : "login"); p.setError(""); }}>
          {p.mode === "login" ? "Need an account? Register" : "Already have an account? Sign in"}
        </button>
        {testLoginEnabled && p.mode === "login" && (
          <button className="test-login-button" type="button" onClick={testLogin} disabled={testBusy}>
            {testBusy ? "Testing…" : "Test Login"}
          </button>
        )}
      </section>
    </main>
  );
}

type DashboardProps = { token: string; onLogout: () => void };

function DashboardView({ token, onLogout }: DashboardProps) {
  const [data, setData] = useState<Dashboard | null>(null);
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [name, setName] = useState("");
  const [target, setTarget] = useState("");
  const [secret, setSecret] = useState("");
  const [error, setError] = useState("");
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  async function refresh() {
    try { setData(await getDashboard(token)); setEndpoints(await getEndpoints(token)); setError(""); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to load dashboard"); }
  }
  useEffect(() => { refresh(); }, []);

  useEffect(() => {
    const socket = new WebSocket(websocketUrl());
    socket.onopen = () => socket.send(JSON.stringify({ token }));
    socket.onmessage = (event) => {
      try { if (JSON.parse(event.data).type === "event_update") refresh(); } catch { /* ignore malformed messages */ }
    };
    return () => socket.close();
  }, [token]);

  async function addEndpoint(e: FormEvent) {
    e.preventDefault(); setError(""); setSecret("");
    try {
      const created = await createEndpoint(token, name, target);
      setSecret(created.signing_secret); setName(""); setTarget(""); await refresh();
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to create endpoint"); }
  }

  async function removeEndpoint(id: string) {
    try { await deleteEndpoint(token, id); await refresh(); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to delete endpoint"); }
  }

  const events = data?.events;
  return (
    <main className="app-shell">
      <header className="topbar"><div><p className="eyebrow">HOOK PLUSE</p><h1>Webhook control center</h1></div><button className="ghost" onClick={onLogout}>Sign out</button></header>
      {error && <div className="alert page-alert">{error}</div>}
      <section className="stats-grid">
        <Stat label="Endpoints" value={data?.endpoints.total ?? 0} hint={`${data?.endpoints.active ?? 0} active`} />
        <Stat label="Events" value={events?.total ?? 0} hint={`${events?.delivered ?? 0} delivered`} />
        <Stat label="Retries" value={events?.retry_scheduled ?? 0} hint="scheduled" />
        <Stat label="Dead letter" value={events?.dlq ?? 0} hint="requires review" />
      </section>
      <MetricsPanel token={token} endpoints={endpoints} onUpdated={refresh} />
      <ApiTestPanel token={token} endpoints={endpoints} onUpdated={refresh} />
      <section className="content-grid">
        <div className="panel"><div className="panel-head"><div><h2>Endpoints</h2><p className="muted">Public ingestion targets managed by your workspace.</p></div></div>
          <form onSubmit={addEndpoint} className="endpoint-form">
            <input placeholder="Endpoint name" value={name} onChange={e => setName(e.target.value)} required />
            <input placeholder="https://example.com/webhook" type="url" value={target} onChange={e => setTarget(e.target.value)} required />
            <button className="primary" type="submit">Add endpoint</button>
          </form>
          {secret && <div className="secret"><strong>Signing secret:</strong> <code>{secret}</code><span>Save this now; it is only returned when the endpoint is created.</span></div>}
          <div className="endpoint-list">
            {endpoints.length === 0 ? <p className="empty">No endpoints yet.</p> : endpoints.map(ep => <div className="endpoint-row" key={ep.id}><div><strong>{ep.name}</strong><span>{ep.target_url}</span></div><button className="danger" onClick={() => removeEndpoint(ep.id)}>Delete</button></div>)}
          </div>
        </div>
        <div className="panel"><div className="panel-head"><div><h2>Recent events</h2><p className="muted">Latest webhook activity.</p></div><button className="ghost" onClick={refresh}>Refresh</button></div>
          <div className="event-list">{data?.recent_events?.length ? data.recent_events.map(event => <button className="event-row event-button" key={event.id} onClick={() => setSelectedEventId(event.id)}><div><strong>{event.event_type}</strong><span>{new Date(event.received_at).toLocaleString()}</span></div><Status value={event.status} /></button>) : <p className="empty">No events received.</p>}</div>
        </div>
      </section>
      {selectedEventId && <EventInspector token={token} eventId={selectedEventId} onClose={() => setSelectedEventId(null)} onReplayed={refresh} />}
    </main>
  );
}

function Stat({ label, value, hint }: { label: string; value: number; hint: string }) { return <div className="stat"><span>{label}</span><strong>{value}</strong><small>{hint}</small></div>; }
function Status({ value }: { value: string }) { return <span className={`status status-${value.toLowerCase()}`}>{value.replaceAll("_", " ")}</span>; }
