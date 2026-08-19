'use client';

import {
  Archive,
  Check,
  ChevronDown,
  CircleStop,
  Database,
  History,
  Pencil,
  Play,
  Plus,
  RefreshCw,
  Server,
  ShieldCheck,
  Star,
  Terminal,
  X,
} from 'lucide-react';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import {
  apiClients,
  unwrapData,
  type ExecutionSession,
  type ExecutionSessionEvent,
  type DatasetSummary,
  type StreamEvent,
} from '@/clients';

type Mode = 'sim' | 'demo' | 'live';
type Action = 'default' | 'start' | 'stop' | 'archive';

const MODE_LABELS: Record<Mode, string> = {
  sim: 'Simulation',
  demo: 'Demo',
  live: 'Live',
};

function statusLabel(value: string): string {
  return value.replaceAll('_', ' ').replace(/^./, (letter) => letter.toUpperCase());
}

function activityLine(event: StreamEvent): string | null {
  if (event.event_type !== 'payload' || typeof event.payload?.line !== 'string') return null;
  return event.payload.line;
}

/** Durable SIM/DEMO/LIVE execution-session cockpit. */
export function SessionRegistryWidget(): React.JSX.Element {
  const [sessions, setSessions] = useState<ExecutionSession[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [mode, setMode] = useState<Mode>('sim');
  const [initialBalance, setInitialBalance] = useState('100000');
  const [leverage, setLeverage] = useState('100');
  const [currency, setCurrency] = useState('USD');
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [datasetId, setDatasetId] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState(false);
  const [events, setEvents] = useState<ExecutionSessionEvent[]>([]);
  const [activity, setActivity] = useState<string[]>([]);
  const [activityPaused, setActivityPaused] = useState(false);
  const activityPausedRef = useRef(false);
  const [activityStatus, setActivityStatus] = useState<'connecting' | 'connected' | 'unavailable'>('connecting');
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const selected = useMemo(
    () => sessions.find((session) => session.session_id === selectedId) ?? sessions[0] ?? null,
    [selectedId, sessions],
  );

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const values = unwrapData(await apiClients.trading.listExecutionSessions());
      setSessions(values);
      setSelectedId((current) =>
        current && values.some((session) => session.session_id === current)
          ? current
          : values[0]?.session_id ?? null,
      );
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Session registry unavailable');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  useEffect(() => {
    let cancelled = false;
    void apiClients.data.datasets()
      .then((response) => {
        if (cancelled) return;
        const values = unwrapData(response);
        setDatasets(values);
        setDatasetId((current) => current || values[0]?.dataset_id || '');
      })
      .catch(() => { if (!cancelled) setDatasets([]); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!selected) {
      setEvents([]);
      return;
    }
    let cancelled = false;
    apiClients.trading.executionSessionEvents(selected.session_id)
      .then((response) => { if (!cancelled) setEvents(unwrapData(response)); })
      .catch(() => { if (!cancelled) setEvents([]); });
    return () => { cancelled = true; };
  }, [selected?.session_id, selected?.version]);

  useEffect(() => {
    activityPausedRef.current = activityPaused;
  }, [activityPaused]);

  useEffect(() => {
    if (!selected) {
      setActivity([]);
      return;
    }
    const controller = new AbortController();
    setActivity([]);
    setActivityStatus('connecting');
    void (async () => {
      try {
        for await (const event of apiClients.trading.executionSessionActivity(selected.session_id, { signal: controller.signal })) {
          if (controller.signal.aborted) return;
          setActivityStatus('connected');
          const line = activityLine(event);
          if (line && !activityPausedRef.current) setActivity((current) => [...current.slice(-249), line]);
        }
      } catch {
        if (!controller.signal.aborted) setActivityStatus('unavailable');
      }
    })();
    return () => controller.abort();
  }, [selected?.session_id]);

  async function create(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    if (!name.trim()) return;
    const dataset = datasets.find((item) => item.dataset_id === datasetId);
    if (mode === 'sim' && !dataset) {
      setError('A verified dataset is required for a SIM session');
      return;
    }
    setBusyAction('create');
    try {
      const created = unwrapData(await apiClients.trading.createExecutionSession({
        name: name.trim(),
        description: description.trim(),
        mode,
        provider: mode === 'sim' ? 'simulation' : 'mt5',
        sim_initial_balance: mode === 'sim' ? initialBalance : null,
        sim_leverage: mode === 'sim' ? Number(leverage) : null,
        sim_account_currency: mode === 'sim' ? currency.toUpperCase() : null,
        dataset_ref: mode === 'sim' ? dataset?.dataset_id : null,
        dataset_revision: mode === 'sim' ? dataset?.revision : null,
        dataset_hash: mode === 'sim' ? dataset?.content_hash : null,
      }));
      setName('');
      setDescription('');
      setShowCreate(false);
      await refresh();
      setSelectedId(created.session_id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Session creation failed');
    } finally {
      setBusyAction(null);
    }
  }

  async function saveEdit(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    if (!selected || !name.trim()) return;
    setBusyAction('edit');
    try {
      await apiClients.trading.updateExecutionSession(selected, {
        name: name.trim(),
        description: description.trim(),
        auto_start: selected.auto_start,
        metadata: selected.metadata,
      });
      setEditing(false);
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Session update failed');
    } finally {
      setBusyAction(null);
    }
  }

  function beginEdit(): void {
    if (!selected) return;
    setName(selected.name);
    setDescription(selected.description);
    setEditing(true);
    setShowCreate(false);
  }

  async function act(action: Action, session: ExecutionSession): Promise<void> {
    if (action === 'archive' && !window.confirm(`Archive “${session.name}”? Its history will be retained.`)) return;
    setBusyAction(`${action}:${session.session_id}`);
    try {
      await apiClients.trading.actOnExecutionSession(action, session);
      await refresh();
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : `Session ${action} failed`);
    } finally {
      setBusyAction(null);
    }
  }

  async function completeSetup(session: ExecutionSession): Promise<void> {
    const dataset = datasets.find((item) => item.dataset_id === datasetId);
    if (!dataset) {
      setError('Select a verified dataset before completing this SIM session');
      return;
    }
    setBusyAction(`configure:${session.session_id}`);
    try {
      await apiClients.trading.completeExecutionSessionConfiguration(session, dataset);
      await refresh();
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'SIM configuration failed');
    } finally {
      setBusyAction(null);
    }
  }

  const counts = (['sim', 'demo', 'live'] as const).map((item) => ({
    mode: item,
    count: sessions.filter((session) => session.mode === item).length,
    running: sessions.some((session) => session.mode === item && session.lifecycle_state === 'running'),
  }));

  return (
    <section className="session-registry" aria-label="Trading sessions">
      <header className="session-registry__hero">
        <div>
          <span className="session-registry__eyebrow"><ShieldCheck size={14} /> Execution environments</span>
          <h2>Trading Sessions</h2>
          <p>Persistent, isolated environments for simulation, demo, and live trading.</p>
        </div>
        <div className="session-registry__hero-actions">
          <button className="session-button session-button--ghost" type="button" onClick={() => void refresh()} disabled={loading}>
            <RefreshCw size={15} className={loading ? 'is-spinning' : ''} /> Refresh
          </button>
          <button className="session-button session-button--primary" type="button" onClick={() => { setShowCreate(true); setEditing(false); setName(''); setDescription(''); }}>
            <Plus size={16} /> New session
          </button>
        </div>
      </header>

      <div className="session-registry__mode-strip" aria-label="Session mode summary">
        {counts.map((item) => <div className={`session-mode-summary session-mode-summary--${item.mode}`} key={item.mode}>
          <span className="session-mode-summary__dot" />
          <div><strong>{MODE_LABELS[item.mode]}</strong><small>{item.count} session{item.count === 1 ? '' : 's'}</small></div>
          <span className="session-mode-summary__state">{item.running ? 'Running' : 'Idle'}</span>
        </div>)}
      </div>

      {error && <div className="session-registry__alert" role="alert">
        <Server size={18} /><div><strong>Session service unavailable</strong><span>{error}</span></div>
        <button type="button" onClick={() => void refresh()}>Try again</button>
      </div>}

      {(showCreate || editing) && <form className="session-editor" onSubmit={(event) => void (editing ? saveEdit(event) : create(event))}>
        <div className="session-editor__title">
          <div><strong>{editing ? 'Edit session' : 'Create a persistent session'}</strong><span>{editing ? 'Update its display information.' : 'Choose an isolated execution environment.'}</span></div>
          <button type="button" aria-label="Close session editor" onClick={() => { setShowCreate(false); setEditing(false); }}><X size={17} /></button>
        </div>
        <div className="session-editor__fields">
          <label><span>Session name</span><input value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. EURUSD research" required /></label>
          <label className="session-editor__description"><span>Description</span><input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Purpose or experiment notes" /></label>
          {!editing && <label><span>Mode</span><select value={mode} onChange={(event) => setMode(event.target.value as Mode)}><option value="sim">SIM</option><option value="demo">DEMO</option><option value="live">LIVE</option></select></label>}
          {!editing && mode === 'sim' && <>
            <label><span>Initial balance</span><input aria-label="Initial balance" inputMode="decimal" value={initialBalance} onChange={(event) => setInitialBalance(event.target.value)} min="0.01" type="number" step="0.01" required /></label>
            <label><span>Leverage</span><div className="session-editor__leverage"><b>1:</b><input aria-label="Leverage" value={leverage} onChange={(event) => setLeverage(event.target.value)} min="1" max="1000" type="number" required /></div></label>
            <label><span>Currency</span><input aria-label="Account currency" value={currency} onChange={(event) => setCurrency(event.target.value.toUpperCase())} maxLength={3} pattern="[A-Z]{3}" required /></label>
            <label><span>Dataset</span><select aria-label="Dataset" value={datasetId} onChange={(event) => setDatasetId(event.target.value)} required>
              {datasets.length === 0 && <option value="">No verified datasets</option>}
              {datasets.map((dataset) => <option key={dataset.dataset_id} value={dataset.dataset_id}>{dataset.label} · {dataset.row_count.toLocaleString()} rows</option>)}
            </select></label>
          </>}
          <button className="session-button session-button--primary" type="submit" disabled={busyAction !== null}>{editing ? <Check size={16} /> : <Plus size={16} />}{editing ? 'Save changes' : 'Create session'}</button>
        </div>
      </form>}

      <div className="session-registry__workspace">
        <div className="session-registry__list-pane">
          <div className="session-pane-heading"><span>Session registry</span><small>{sessions.length} total</small></div>
          {loading && sessions.length === 0 ? <div className="session-registry__loading"><RefreshCw size={22} className="is-spinning" /><span>Loading persistent sessions…</span></div> : null}
          {!loading && sessions.length === 0 && !error ? <div className="session-registry__empty">
            <div className="session-registry__empty-icon"><Database size={28} /></div>
            <h3>No trading sessions yet</h3>
            <p>Create a durable SIM, DEMO, or LIVE environment. Controls appear here as soon as it is registered.</p>
            <button className="session-button session-button--primary" type="button" onClick={() => setShowCreate(true)}><Plus size={16} /> Create first session</button>
          </div> : null}
          <div className="session-card-list">
            {sessions.map((session) => <button
              type="button"
              key={session.session_id}
              className={`session-card session-card--${session.mode}${selected?.session_id === session.session_id ? ' is-selected' : ''}`}
              onClick={() => setSelectedId(session.session_id)}
            >
              <span className="session-card__mode">{session.mode.toUpperCase()}</span>
              <span className="session-card__body"><strong>{session.name}</strong><small>{session.provider} · {statusLabel(session.lifecycle_state)}</small></span>
              <span className={`session-status-dot session-status-dot--${session.lifecycle_state}`} />
              {session.is_default && <span className="session-card__default"><Star size={12} fill="currentColor" /> Default</span>}
              <ChevronDown className="session-card__chevron" size={15} />
            </button>)}
          </div>
        </div>

        <div className="session-registry__detail-pane">
          {!selected ? <div className="session-registry__detail-empty"><ShieldCheck size={34} /><strong>Select a session</strong><span>Session controls and evidence will appear here.</span></div> : <>
            <div className="session-detail__header">
              <div><span className={`session-detail__mode session-detail__mode--${selected.mode}`}>{selected.mode.toUpperCase()}</span><h3>{selected.name}</h3><p>{selected.description || 'No description supplied.'}</p></div>
              <button className="session-icon-button" type="button" aria-label="Edit session" onClick={beginEdit}><Pencil size={16} /></button>
            </div>

            <div className="session-control-bar" aria-label="Session controls">
              {selected.lifecycle_state === 'running' ? <button className="session-button session-button--stop" disabled={busyAction !== null} type="button" onClick={() => void act('stop', selected)}><CircleStop size={16} /> Stop session</button> : <button className="session-button session-button--start" disabled={busyAction !== null} type="button" onClick={() => void act('start', selected)}><Play size={16} fill="currentColor" /> Start session</button>}
              <button className="session-button session-button--secondary" disabled={busyAction !== null || selected.is_default} type="button" onClick={() => void act('default', selected)}><Star size={16} /> {selected.is_default ? 'Default session' : 'Make default'}</button>
              <button className="session-button session-button--danger" disabled={busyAction !== null || selected.lifecycle_state === 'running' || selected.is_default} type="button" onClick={() => void act('archive', selected)}><Archive size={16} /> Archive</button>
            </div>

            {selected.mode === 'sim' && (!selected.provider_account_ref || !selected.simulation_session_id || !selected.dataset_ref) && <div className="session-legacy-setup" role="status">
              <div><strong>SIM setup incomplete</strong><span>{selected.lifecycle_state === 'running' ? 'Stop this legacy session before assigning its verified dataset and identities.' : 'Choose a verified dataset. Account Name and Simulation ID will be assigned automatically.'}</span></div>
              <select aria-label="Legacy session dataset" value={datasetId} onChange={(event) => setDatasetId(event.target.value)}>
                {datasets.length === 0 && <option value="">No verified datasets</option>}
                {datasets.map((dataset) => <option key={dataset.dataset_id} value={dataset.dataset_id}>{dataset.label} · {dataset.row_count.toLocaleString()} rows</option>)}
              </select>
              <button className="session-button session-button--primary" type="button" disabled={busyAction !== null || selected.lifecycle_state === 'running' || !datasetId} onClick={() => void completeSetup(selected)}>Complete SIM setup</button>
            </div>}

            <div className="session-detail__facts">
              <div><span>Status</span><strong><i className={`session-status-dot session-status-dot--${selected.lifecycle_state}`} />{statusLabel(selected.lifecycle_state)}</strong></div>
              <div><span>Provider</span><strong>{selected.provider}</strong></div>
              <div><span>Auto start</span><strong>{selected.auto_start ? 'Enabled' : 'Disabled'}</strong></div>
              <div><span>Revision</span><strong>v{selected.version}</strong></div>
            </div>

            <details className="session-detail__section" open><summary><Database size={15} /> Session data <ChevronDown size={14} /></summary><dl>
              <div><dt>Session ID</dt><dd>{selected.session_id}</dd></div>
              <div><dt>Account name</dt><dd>{selected.provider_account_ref ?? 'Assigned on start'}</dd></div>
              <div><dt>Simulation ID</dt><dd>{selected.simulation_session_id ?? 'Not assigned'}</dd></div>
              <div><dt>Dataset</dt><dd>{selected.dataset_ref ?? 'Not assigned'}{selected.dataset_ref ? ' · Active' : ''}</dd></div>
              <div><dt>Opening balance</dt><dd>{selected.sim_initial_balance == null ? 'Provider-authored' : `${selected.sim_account_currency ?? 'USD'} ${Number(selected.sim_initial_balance).toLocaleString('en-US', { minimumFractionDigits: 2 })}`}</dd></div>
              <div><dt>Leverage</dt><dd>{selected.sim_leverage == null ? 'Provider-authored' : `1:${selected.sim_leverage}`}</dd></div>
              <div><dt>Last reconciled</dt><dd>{selected.last_reconciled_at ? new Date(selected.last_reconciled_at).toLocaleString() : 'Never'}</dd></div>
            </dl></details>

            <details className="session-detail__section"><summary><History size={15} /> Lifecycle history <span>{events.length}</span><ChevronDown size={14} /></summary><ol className="session-event-list">
              {events.length === 0 ? <li className="session-event-list__empty">No lifecycle events available.</li> : events.map((event) => <li key={event.event_id}><span className="session-event-list__marker" /><div><strong>{statusLabel(event.event_type)}</strong><small>{new Date(event.occurred_at).toLocaleString()}</small></div></li>)}
            </ol></details>

            <details className="session-detail__section session-activity" open><summary><Terminal size={15} /> Live activity <span>{activityStatus}</span><ChevronDown size={14} /></summary>
              <div className="session-activity__controls">
                <span>File-backed · redacted · not duplicated in the database</span>
                <button type="button" onClick={() => setActivityPaused((value) => !value)}>{activityPaused ? 'Resume' : 'Pause'}</button>
                <button type="button" onClick={() => setActivity([])}>Clear</button>
              </div>
              <pre className="session-activity__console" role="log" aria-live="polite">{activity.length ? activity.join('\n') : activityStatus === 'unavailable' ? 'Activity stream unavailable.' : 'Waiting for session activity…'}</pre>
            </details>
          </>}
        </div>
      </div>
    </section>
  );
}
