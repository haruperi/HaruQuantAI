import { useEffect, useRef, useState } from 'react';
import { ArrowRight, BookOpen, CircleHelp, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useHostConnection } from '../../host/HostConnection';
import type { ModuleId } from '../../host/types';
import { getPathForModule } from '../../host/router';
import { homeClient, type AboutInfo, type DiagnosticsInfo, type HomeIndex, type ReleaseInfo } from './homeClient';
import content from './homeContent.json';
import './HomeScreen.css';

const workspaces: Record<string, ModuleId> = {
  datamanager: 'datamanager', algowizard: 'algowizard', builder: 'builder', projects: 'projects',
  retester: 'retester', optimizer: 'optimizer', composer: 'composer', portfolio: 'portfolio',
  codeeditor: 'codeeditor', neuralnet: 'neuralnet', mtanalyzer: 'mtanalyzer',
};
interface Snapshot { index: HomeIndex | null; about: AboutInfo | null; error: string; loading: boolean }

export function HomeScreen() {
  const { status } = useHostConnection();
  const navigate = useNavigate();
  const [snapshot, setSnapshot] = useState<Snapshot>({ index: null, about: null, error: '', loading: false });
  const [retry, setRetry] = useState(0);
  const [release, setRelease] = useState<ReleaseInfo | null>(null);
  const [diagnostics, setDiagnostics] = useState<DiagnosticsInfo | null>(null);
  const [pending, setPending] = useState<'updates' | 'diagnostics' | null>(null);
  const [actionError, setActionError] = useState('');
  const actionRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    actionRef.current?.abort(); actionRef.current = null;
    setRelease(null); setDiagnostics(null); setPending(null); setActionError('');
    setSnapshot({ index: null, about: null, error: '', loading: status === 'online' });
    if (status === 'online') {
      const client = homeClient({ signal: controller.signal });
      void Promise.allSettled([client.index(), client.about()]).then(([index, about]) => {
        if (!controller.signal.aborted) setSnapshot({
          index: index.status === 'fulfilled' ? index.value : null, about: about.status === 'fulfilled' ? about.value : null,
          error: index.status === 'rejected' || about.status === 'rejected' ? 'Some host information could not be loaded.' : '', loading: false,
        });
      });
    }
    return () => { controller.abort(); actionRef.current?.abort(); };
  }, [status, retry]);

  async function inspect(kind: 'updates' | 'diagnostics') {
    if (status !== 'online' || actionRef.current) return;
    const controller = new AbortController(); actionRef.current = controller;
    setPending(kind); setActionError('');
    try {
      const client = homeClient({ signal: controller.signal });
      if (kind === 'updates') { const value = await client.updates(); if (!controller.signal.aborted) setRelease(value); }
      else { const value = await client.diagnostics(); if (!controller.signal.aborted) setDiagnostics(value); }
    } catch {
      if (!controller.signal.aborted) setActionError('The request could not be completed. Reconnect or try again.');
    } finally {
      if (actionRef.current === controller) { actionRef.current = null; setPending(null); }
    }
  }

  const online = status === 'online', index = online ? snapshot.index : null, about = online ? snapshot.about : null;
  const openWorkspace = (id: string) => { const module = workspaces[id]; if (module) navigate(getPathForModule(module)); };
  return (
    <main className="home-landing" aria-label="Home workspace">
      <header className="home-welcome"><div><span className="home-eyebrow">HaruQuantAI · Getting started</span><h1>{content.title}</h1><p>{content.description}</p></div><span className={`home-connection home-connection-${status}`}>Host {status}</span></header>
      {!online && <p className="home-feedback" role="status">{status === 'locked' ? 'Connect to the host to see your projects and system information.' : status === 'connecting' ? 'Connecting to the host… Local guides are ready to read.' : 'The host is offline. Local guides remain available.'}</p>}
      {online && snapshot.loading && <p role="status">Loading host information…</p>}
      {online && snapshot.error && <div className="home-feedback" role="alert">{snapshot.error} <button onClick={() => setRetry(value => value + 1)}>Retry host information</button></div>}
      <section className="home-quick" aria-label="Quick start">{content.actions.map(action => <button key={action.id} onClick={() => openWorkspace(action.id)}><span>{action.label}</span><ArrowRight size={17} aria-hidden="true" /></button>)}</section>
      <div className="home-columns">
        <section className="home-panel home-guides" aria-labelledby="home-guide-title">
          <div className="home-section-title"><BookOpen size={19} aria-hidden="true" /><h2 id="home-guide-title">A first research workflow</h2><span>Available offline</span></div>
          {content.tutorials.map(guide => <article className="home-guide" key={guide.id}><h3>{guide.title}</h3><p>{guide.summary}</p><details><summary>Read guide</summary><p>{guide.body}</p><button onClick={() => openWorkspace(guide.workspace)}>Open workspace <ArrowRight size={14} aria-hidden="true" /></button></details></article>)}
        </section>
        <section className="home-panel" aria-labelledby="home-projects-title">
          <h2 id="home-projects-title">Recent projects</h2><p className="home-muted">Host-saved summaries, ordered by last activity.</p>
          {!online ? <p>Connect to view recent projects.</p> : snapshot.loading ? <p>Loading projects…</p> : !index ? <p>Project information is unavailable.</p> : index.recent_projects.length === 0 ? <div className="home-empty"><h3>No recent projects yet</h3><p>Projects will appear here when their workspace saves a host summary.</p></div> : <ul className="home-projects">{index.recent_projects.map(project => <li key={project.id}><strong>{project.name}</strong><span className="home-muted">Last activity: <time dateTime={project.last_activity}>{project.last_activity}</time></span><button disabled={!workspaces[project.workspace]} onClick={() => openWorkspace(project.workspace)}>Open workspace</button><small>Specific project reopening depends on its workspace.</small></li>)}</ul>}
        </section>
        <section className="home-panel home-about" aria-labelledby="home-about-title">
          <h2 id="home-about-title">About this installation</h2>
          {about ? <><dl><dt>Application</dt><dd>{about.application}</dd><dt>Host-reported version</dt><dd>{about.version}</dd><dt>Host-reported build timestamp</dt><dd>{about.build_timestamp}</dd><dt>Runtime</dt><dd>{about.runtime}</dd><dt>License</dt><dd>{about.license.state}: {about.license.reason}</dd></dl><p className="home-muted">Metadata is reported by the host; independent build provenance is not established.</p></> : <p>{online ? 'Host metadata is not available yet.' : 'Connect to view host metadata.'}</p>}
          <div className="home-actions"><button disabled={!online || pending !== null} onClick={() => void inspect('updates')}><RefreshCw size={15} aria-hidden="true" />{pending === 'updates' ? 'Checking…' : 'Check for updates'}</button><button disabled={!online || pending !== null} onClick={() => void inspect('diagnostics')}>{pending === 'diagnostics' ? 'Inspecting…' : 'Inspect diagnostics'}</button></div>
          {online && actionError && <p role="alert">{actionError}</p>}
          {online && release && <div className="home-inspection" role="status"><h3>Release information</h3><p>{release.state === 'available' ? release.update_available === true ? `Version ${release.latest_version} is available.` : 'No newer stable release was reported.' : `${release.state}: ${release.reason}`}</p><small>Checked: {release.checked_at}</small>{release.changelog && <pre>{release.changelog}</pre>}</div>}
          {online && diagnostics && <div className="home-inspection"><h3>System diagnostics</h3><dl><dt>System</dt><dd>{diagnostics.status}</dd><dt>Database</dt><dd>{diagnostics.database.exists ? diagnostics.database.error ? 'Degraded' : 'Available' : 'Missing'}</dd><dt>Database path</dt><dd>{diagnostics.database.path}</dd><dt>Available memory</dt><dd>{(diagnostics.hardware.ram_available_bytes / 1024 ** 3).toFixed(2)} GiB of {(diagnostics.hardware.ram_total_bytes / 1024 ** 3).toFixed(2)} GiB</dd>{Object.entries(diagnostics.directories).map(([key, path]) => <div className="home-directory" key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{path}</dd></div>)}</dl></div>}
        </section>
      </div>
      <section className="home-panel home-help" aria-labelledby="home-help-title"><div className="home-section-title"><CircleHelp size={19} aria-hidden="true" /><h2 id="home-help-title">Local help</h2></div>{content.help.map(topic => <details key={topic.id}><summary>{topic.title}</summary><p>{topic.body}</p></details>)}</section>
    </main>
  );
}
