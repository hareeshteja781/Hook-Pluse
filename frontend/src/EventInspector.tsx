import Editor from "@monaco-editor/react";
import { useEffect, useState } from "react";
import { getEvent, replayEvent } from "./api";
import type { EventAttempt, EventDetail } from "./api";

type Props = { token: string; eventId: string; onClose: () => void; onReplayed: () => void };

export default function EventInspector({ token, eventId, onClose, onReplayed }: Props) {
  const [event, setEvent] = useState<EventDetail | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getEvent(token, eventId).then(setEvent).catch(err => setError(err instanceof Error ? err.message : "Unable to load event"));
  }, [token, eventId]);

  async function replay() {
    setBusy(true); setError("");
    try { await replayEvent(token, eventId); onReplayed(); }
    catch (err) { setError(err instanceof Error ? err.message : "Replay failed"); }
    finally { setBusy(false); }
  }

  if (error) return <div className="inspector-backdrop"><div className="inspector"><button className="ghost" onClick={onClose}>Close</button><div className="alert">{error}</div></div></div>;
  if (!event) return <div className="inspector-backdrop"><div className="inspector"><p className="muted">Loading event…</p></div></div>;

  const pretty = (value: unknown) => JSON.stringify(value, null, 2);
  return <div className="inspector-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) onClose(); }}>
    <section className="inspector">
      <div className="inspector-head"><div><p className="eyebrow">EVENT INSPECTOR</p><h2>{event.event_type || "webhook"}</h2><p className="muted">{event.id}</p></div><div className="inspector-actions"><span className="status">{event.status.replaceAll("_", " ")}</span><button className="primary" disabled={busy} onClick={replay}>{busy ? "Replaying…" : "Replay"}</button><button className="ghost" onClick={onClose}>Close</button></div></div>
      <div className="inspector-grid">
        <div className="editor-panel"><div className="editor-title">Payload</div><Editor height="300px" defaultLanguage="json" value={pretty(event.payload)} theme="vs-dark" options={{ readOnly: true, minimap: { enabled: false }, fontSize: 13, padding: { top: 12 } }} /></div>
        <div className="editor-panel"><div className="editor-title">Headers</div><Editor height="300px" defaultLanguage="json" value={pretty(event.headers)} theme="vs-dark" options={{ readOnly: true, minimap: { enabled: false }, fontSize: 13, padding: { top: 12 } }} /></div>
      </div>
      <div className="inspector-meta">
        <div><span>Idempotency key</span><code>{event.idempotency_key}</code></div>
        <div><span>Body SHA-256</span><code>{event.body_hash}</code></div>
        <div><span>Received</span><code>{new Date(event.received_at).toLocaleString()}</code></div>
        {event.replay_of_id && <div><span>Replayed from</span><code>{event.replay_of_id}</code></div>}
      </div>
      <div className="attempts"><h3>Delivery attempts</h3>{event.attempts.length ? event.attempts.map((attempt: EventAttempt) => <div className="attempt" key={attempt.id}><strong>Attempt {attempt.attempt_number}</strong><span>{attempt.http_status ?? "transport error"}</span><span>{attempt.duration_ms ?? 0} ms</span><span>{attempt.error || attempt.response_body || "No response body"}</span></div>) : <p className="muted">No delivery attempts recorded yet.</p>}</div>
    </section>
  </div>;
}

