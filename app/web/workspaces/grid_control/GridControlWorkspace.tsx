import { useEffect, useMemo, useState } from 'react';
import { RefreshCw, TriangleAlert } from 'lucide-react';
import { Button, Modal, Select } from '../../common/components/ui';
import { useAppStore } from '../../shell/store';
import type { Job } from '../../shell/types';
import { ClusterPanel } from './ClusterPanel';
import { GridJobPresentation } from './jobPresentation';

export interface GridJobRow {
  id: string;
  groupId: string;
  type: 'Continuous' | 'One time';
  status: string;
  created: string;
  started: string;
  duration: string;
  progress: string;
  error?: string;
}

export interface GridSections {
  running: GridJobRow[];
  waiting: GridJobRow[];
  finished: GridJobRow[];
}

const statusTime = (timeStr?: string) =>
  timeStr ? timeStr.replace('T', ' ').slice(0, 19) : '—';

function calculateDuration(job: Job): string {
  if (['queued', 'waiting'].includes(job.status)) {
    return '—';
  }
  if (job.startedAt) {
    const start = new Date(job.startedAt).getTime();
    const end = job.finishedAt ? new Date(job.finishedAt).getTime() : Date.now();
    const elapsedSec = Math.max(0, Math.floor((end - start) / 1000));
    const mins = String(Math.floor(elapsedSec / 60)).padStart(2, '0');
    const secs = String(elapsedSec % 60).padStart(2, '0');
    return `00:${mins}:${secs}`;
  }
  return job.status === 'running' ? 'Running' : '—';
}

export function jobToGridRow(job: Job, key: string): GridJobRow {
  const time = statusTime(job.startedAt);
  const isWaiting = ['queued', 'idle', 'waiting'].includes(job.status);
  const isFinished = ['completed', 'failed', 'cancelled', 'stopped'].includes(job.status);
  const statusStr =
    job.status === 'completed'
      ? 'Success'
      : job.status === 'failed'
        ? 'Error'
        : GridJobPresentation.state(isWaiting);

  return {
    id: job.id || key,
    groupId: job.jobGroupId || key,
    type: GridJobPresentation.kind(Boolean(job.blocking)),
    status: statusStr,
    created: statusTime(job.createdAt || job.startedAt),
    started: isWaiting ? '—' : time,
    duration: calculateDuration(job),
    progress: GridJobPresentation.progress(job.progress ?? -1),
    error: job.status === 'failed' ? (job.message || 'The compute job failed.') : undefined,
  };
}

export function classifyGridJobs(jobs: Record<string, Job>): GridSections {
  const rows = Object.entries(jobs).map(([key, job]) => jobToGridRow(job, key));
  const running = rows.filter(row => ['Running', 'Paused'].includes(row.status));
  const waiting = rows.filter(row => ['Waiting', 'Queued', 'Idle'].includes(row.status));
  const finished = rows
    .filter(row => ['Success', 'Error', 'Cancelled', 'Stopped'].includes(row.status))
    .slice(0, 100);

  return { running, waiting, finished };
}

function EmptyRow({ columns, children }: { columns: number; children: string }) {
  return (
    <tr>
      <td colSpan={columns} className="grid-empty">
        {children}
      </td>
    </tr>
  );
}

function GridPanel({
  title,
  rows,
  kind,
  onError,
}: {
  title: string;
  rows: GridJobRow[];
  kind: 'running' | 'waiting' | 'finished';
  onError: (row: GridJobRow) => void;
}) {
  return (
    <fieldset className="grid-control-panel" data-testid={`grid-panel-${kind}`}>
      <legend>{title}</legend>
      {kind !== 'finished' && <span className="grid-records">Records: {rows.length}</span>}
      <div className="plain-table-wrap">
        <table className="plain-table grid-jobs">
          <thead>
            <tr>
              <th>Job ID</th>
              <th>Job group ID</th>
              <th>Type</th>
              {kind === 'running' && <th>Status</th>}
              <th>Created</th>
              {kind !== 'waiting' && <th>Started</th>}
              {kind === 'running' && <th>Run time</th>}
              {kind === 'finished' && <th>Duration</th>}
              {kind !== 'waiting' && <th>{kind === 'finished' ? 'Status' : 'Progress'}</th>}
            </tr>
          </thead>
          <tbody>
            {rows.length ? (
              rows.map(row => (
                <tr key={row.id} className={row.error ? 'grid-job-error' : ''}>
                  <td>{row.id}</td>
                  <td>{row.groupId}</td>
                  <td>{row.type}</td>
                  {kind === 'running' && <td>{row.status}</td>}
                  <td>{row.created}</td>
                  {kind !== 'waiting' && <td>{row.started}</td>}
                  {kind === 'running' && <td>{row.duration}</td>}
                  {kind === 'finished' && <td>{row.duration}</td>}
                  {kind !== 'waiting' && (
                    <td>
                      {row.error ? (
                        <button className="grid-error-link" onClick={() => onError(row)}>
                          Error
                        </button>
                      ) : kind === 'finished' ? (
                        row.status
                      ) : (
                        row.progress
                      )}
                    </td>
                  )}
                </tr>
              ))
            ) : (
              <EmptyRow columns={kind === 'running' ? 8 : kind === 'waiting' ? 4 : 7}>
                {kind === 'running'
                  ? 'No jobs in progress.'
                  : kind === 'waiting'
                    ? 'No waiting jobs.'
                    : 'No finished jobs.'}
              </EmptyRow>
            )}
          </tbody>
        </table>
      </div>
    </fieldset>
  );
}

export function GridControlWorkspace() {
  const jobs = useAppStore(s => s.jobs);
  const computeNodes = useAppStore(s => s.computeNodes);
  const addComputeNode = useAppStore(s => s.addComputeNode);
  const removeComputeNode = useAppStore(s => s.removeComputeNode);

  const sections = useMemo(() => classifyGridJobs(jobs), [jobs]);
  const [refreshedAt, setRefreshedAt] = useState(() => new Date());
  const [error, setError] = useState<GridJobRow | null>(null);

  useEffect(() => {
    if (!GridJobPresentation.can_refresh('GRIDCONTROL')) {
      return;
    }
    const timer = window.setInterval(
      () => setRefreshedAt(new Date()),
      GridJobPresentation.interval_ms(),
    );
    return () => window.clearInterval(timer);
  }, []);

  const refresh = () => setRefreshedAt(new Date());

  return (
    <section className="header-app grid-control" aria-labelledby="grid-control-title">
      <div className="grid-control-scroll">
        <h1 id="grid-control-title">Grid engine overview</h1>

        <fieldset className="grid-control-panel grid-control-toolbar">
          <span>Auto-refresh every {GridJobPresentation.interval_ms() / 1000} seconds</span>
          <label>
            Grid
            <Select value="Local grid" onChange={() => undefined}>
              <option>Local grid</option>
            </Select>
          </label>
          <Button title="Refresh data" aria-label="Refresh data" onClick={refresh}>
            <RefreshCw /> Refresh
          </Button>
          <small>Last refreshed {refreshedAt.toLocaleTimeString()}</small>
        </fieldset>

        <ClusterPanel
          nodes={computeNodes}
          onAddNode={addComputeNode}
          onRemoveNode={removeComputeNode}
        />

        <GridPanel
          title="Jobs in progress"
          rows={sections.running}
          kind="running"
          onError={setError}
        />
        <GridPanel
          title="Waiting jobs"
          rows={sections.waiting}
          kind="waiting"
          onError={setError}
        />
        <GridPanel
          title="Last 100 finished jobs"
          rows={sections.finished}
          kind="finished"
          onError={setError}
        />
      </div>

      {error && (
        <Modal
          title="Errors"
          onClose={() => setError(null)}
          width={560}
          footer={<Button onClick={() => setError(null)}>Close</Button>}
        >
          <div className="grid-error-dialog">
            <TriangleAlert />
            <div>
              <strong>{error.id}</strong>
              <p>{error.error}</p>
            </div>
          </div>
        </Modal>
      )}
    </section>
  );
}
