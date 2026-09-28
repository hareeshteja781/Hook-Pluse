import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { getMetrics, sendSimulator } from "./api";
import type { Endpoint, Metrics } from "./api";

type Props = { token: string; endpoints: Endpoint[]; onUpdated: () => void };

export default function MetricsPanel({ token, endpoints, onUpdated }: Props) {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [endpointId, setEndpointId] = useState("");
  const [count, setCount] = useState(5);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getMetrics(token).then(setMetrics).catch(err => setError(err instanceof Error ? err.message : "Unable to load metrics"));
  }, [token]);

  async function run(e: FormEvent) {
    e.preventDefault(); if (!endpointId) return; setBusy(true); setMessage(""); setError("");
    try {
      const result = await sendSimulator(token, endpointId, count, "simulator.event");
      setMessage(`${result.created} events created and ${result.dispatched} queued.`);
      setMetrics(await getMetrics(token)); onUpdated();
    } catch (err) { setError(err instanceof Error ? err.message : "Simulator failed"); }
    finally { setBusy(false); }
  }
  return <section className="panel metrics-panel">
    <div className="panel-head"><div><h2>Metrics & simulator</h2><p className="muted">Generate traffic and inspect delivery performance.</p></div></div>
    <div className="metric-cards">
      <div><span>Success rate</span><strong>{metrics?.delivery.success_rate ?? 0}%</strong></div>
      <div><span>Avg latency</span><strong>{metrics?.delivery.avg_latency_ms ?? 0} ms</strong></div>
      <div><span>Attempts</span><strong>{metrics?.delivery.attempts ?? 0}</strong></div>
      <div><span>DLQ</span><strong>{metrics?.events.dlq ?? 0}</strong></div>
    </div>
    <form className="simulator-form" onSubmit={run}>
      <select value={endpointId} onChange={e => setEndpointId(e.target.value)} required>
        <option value="">Choose endpoint</option>
        {endpoints.map(ep => <option key={ep.id} value={ep.id}>{ep.name}</option>)}
      </select>
      <input type="number" min="1" max="100" value={count} onChange={e => setCount(Number(e.target.value))} />
      <button className="primary" disabled={busy || !endpoints.length}>{busy ? "Sending…" : "Send test events"}</button>
    </form>
    {message && <div className="success-note">{message}</div>}
    {error && <div className="alert">{error}</div>}
  </section>;
}
