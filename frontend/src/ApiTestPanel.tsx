import { useState } from "react";
import {
  getDashboard,
  getEndpoints,
  getEvent,
  getMe,
  getMetrics,
  healthCheck,
  login,
  replayEvent,
  sendSimulator,
} from "./api";
import type { Endpoint } from "./api";

type Props = { token: string; endpoints: Endpoint[]; latestEventId: string | null; onUpdated: () => void };

export default function ApiTestPanel({ token, endpoints, latestEventId, onUpdated }: Props) {
  const [results, setResults] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState("");
  const [eventId, setEventId] = useState("");
  const [replayResult, setReplayResult] = useState("");
  const [testCount, setTestCount] = useState(1);

  function pass(name: string, detail: string) {
    setResults(prev => ({ ...prev, [name]: `PASS — ${detail}` }));
  }
  function fail(name: string, err: unknown) {
    setResults(prev => ({ ...prev, [name]: `FAIL — ${err instanceof Error ? err.message : String(err)}` }));
  }
  async function run(name: string, fn: () => Promise<string>) {
    setBusy(name);
    try { pass(name, await fn()); }
    catch (err) { fail(name, err); }
    finally { setBusy(""); }
  }

  async function testAuth() {
    await run("Auth", async () => {
      const result = await login("test@hookpluse.com", "HookPluseTest123!");
      const me = await getMe(result.access_token);
      return me.email;
    });
  }

  async function testDashboard() {
    await run("Dashboard / DB", async () => {
      const data = await getDashboard(token);
      return `${data.endpoints.total} endpoints, ${data.events.total} events`;
    });
  }
  async function testEndpoints() {
    await run("Endpoints API", async () => {
      const data = await getEndpoints(token);
      onUpdated();
      return `${data.length} endpoint(s)`;
    });
  }

  async function testMetrics() {
    await run("Metrics API", async () => {
      const data = await getMetrics(token);
      return `${data.delivery.success_rate}% success rate`;
    });
  }

  async function testSimulator() {
    if (!endpoints.length) {
      fail("Simulator", "Create an endpoint first");
      return;
    }
    await run("Simulator", async () => {
      const result = await sendSimulator(token, endpoints[0].id, testCount, "ui.test");
      onUpdated();
      return `${result.created} created, ${result.dispatched} queued`;
    });
  }

  function useLatestEvent() {
    if (latestEventId) setEventId(latestEventId);
    else fail("Event detail", "No event available yet. Run the simulator after Redis is running.");
  }

  async function testEvent() {
    if (!eventId.trim()) {
      fail("Event detail", "Enter an event ID");
      return;
    }
    await run("Event detail", async () => {
      const event = await getEvent(token, eventId.trim());
      return `${event.status} — ${event.event_type ?? "event"}`;
    });
  }

  async function testReplay() {
    if (!eventId.trim()) {
      setReplayResult("Enter an event ID first");
      return;
    }
    setBusy("Replay");
    setReplayResult("");
    try {
      const result = await replayEvent(token, eventId.trim());
      setReplayResult(`PASS — replay ${result.event_id}`);
      onUpdated();
    } catch (err) {
      setReplayResult(`FAIL — ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setBusy("");
    }
  }
  async function runCore() {
    setBusy("Core");
    setResults({});
    try {
      const health = await healthCheck();
      const me = await getMe(token);
      const dashboard = await getDashboard(token);
      const metrics = await getMetrics(token);
      const eps = await getEndpoints(token);
      setResults({
        Core: `PASS — API ${health.status}; user ${me.email}; ${dashboard.endpoints.total} endpoints; ${metrics.events.total} events; ${eps.length} endpoint(s)`,
      });
      onUpdated();
    } catch (err) {
      fail("Core", err);
    } finally {
      setBusy("");
    }
  }

  return (
    <section className="panel api-test-panel">
      <div className="panel-head">
        <div><h2>Developer Test Console</h2><p className="muted">Test Hook Pluse APIs without leaving the dashboard.</p></div>
        <button className="ghost" onClick={runCore} disabled={busy !== ""}>{busy === "Core" ? "Running…" : "Run core tests"}</button>
      </div>
      <div className="test-grid">
        <TestCard name="Health" result={results.Health} busy={busy === "Health"} onClick={() => run("Health", async () => (await healthCheck()).status)} />
        <TestCard name="Auth" result={results.Auth} busy={busy === "Auth"} onClick={testAuth} />
        <TestCard name="Dashboard / DB" result={results["Dashboard / DB"]} busy={busy === "Dashboard / DB"} onClick={testDashboard} />
        <TestCard name="Endpoints API" result={results["Endpoints API"]} busy={busy === "Endpoints API"} onClick={testEndpoints} />
        <TestCard name="Metrics API" result={results["Metrics API"]} busy={busy === "Metrics API"} onClick={testMetrics} />
        <div className="test-card">
          <div><strong>Simulator</strong><small>Generate test events</small></div>
          <div className="test-inline"><input type="number" min="1" max="100" value={testCount} onChange={e => setTestCount(Number(e.target.value))} /><button className="ghost" onClick={testSimulator} disabled={busy !== ""}>{busy === "Simulator" ? "…" : "Run"}</button></div>
          {results.Simulator && <small className={results.Simulator.startsWith("PASS") ? "test-pass" : "test-fail"}>{results.Simulator}</small>}
        </div>
      </div>
      <div className="event-test">
        <div>
          <label>Event ID<input value={eventId} onChange={e => setEventId(e.target.value)} placeholder="Event UUID (e.g. 550e8400-e29b-41d4-a716-446655440000)" /></label>
          <div className="test-inline"><button className="ghost" type="button" onClick={useLatestEvent} disabled={!latestEventId}>Use latest event</button>{eventId && <small className="test-hint">Use the same ID for detail and replay tests.</small>}</div>
        </div>
        <button className="ghost" onClick={testEvent} disabled={busy !== ""}>{busy === "Event detail" ? "Testing…" : "Test event detail"}</button>
        <button className="ghost" onClick={testReplay} disabled={busy !== ""}>{busy === "Replay" ? "Testing…" : "Test replay"}</button>
      </div>
      {results["Event detail"] && <div className={results["Event detail"].startsWith("PASS") ? "test-result test-pass" : "test-result test-fail"}>{results["Event detail"]}</div>}
      {replayResult && <div className={replayResult.startsWith("PASS") ? "test-result test-pass" : "test-result test-fail"}>{replayResult}</div>}
      {results.Core && <div className={results.Core.startsWith("PASS") ? "test-result test-pass" : "test-result test-fail"}>{results.Core}</div>}
    </section>
  );
}

function TestCard({ name, result, busy, onClick }: { name: string; result?: string; busy: boolean; onClick: () => void }) {
  return <div className="test-card">
    <div><strong>{name}</strong><small>API check</small></div>
    <button className="ghost" onClick={onClick} disabled={busy}>{busy ? "…" : "Run"}</button>
    {result && <small className={result.startsWith("PASS") ? "test-pass" : "test-fail"}>{result}</small>}
  </div>;
}
