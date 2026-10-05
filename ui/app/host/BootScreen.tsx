/**
 * Full-screen boot presentation driven by the backend's stage snapshot.
 * This component owns no initialization, transport, or persistent state. Its
 * progress count measures reported terminal outcomes, including unavailable or
 * failed stages; a full bar therefore does not mean every provider succeeded.
 */
import type { BootSnapshot } from './transport';

/**
 * Render host state, reported-stage progress, and individual stage outcomes.
 * @param props.snapshot - Current authoritative snapshot supplied by the host connection.
 * @returns Accessible status section; rendering performs no host operations.
 */
export function BootScreen({ snapshot }: { snapshot: BootSnapshot }) {
  const finished = snapshot.stages.filter(stage => !['pending', 'running'].includes(stage.outcome)).length;
  return <section role="status" aria-label="Host startup" className="fixed inset-0 z-50 overflow-auto bg-slate-950 p-8 text-slate-100">
    <h1>Starting HaruQuantAI</h1>
    <p>{snapshot.state} · {finished} / {snapshot.stages.length} phases reported</p>
    <progress value={finished} max={snapshot.stages.length} aria-label="Boot progress" />
    <ul>{snapshot.stages.map(stage => <li key={stage.stage}>
      <strong>{stage.label}</strong> — {stage.outcome}
      {stage.reason && ` (${stage.reason.replaceAll('_', ' ')})`}
    </li>)}</ul>
  </section>;
}
