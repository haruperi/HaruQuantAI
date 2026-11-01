import { useCallback, useEffect, useRef, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { homeClient } from '../homeClient';
import { useProjectBinding } from '../projectController';

export type EngineRunStatus = 'idle' | 'queued' | 'running' | 'paused' | 'complete' | 'cancelled' | 'stopped' | 'interrupted' | 'error';
export interface EngineRunHandle {
  status: EngineRunStatus; step: number; log: string[]; clearOnStart: boolean;
  setClearOnStart: Dispatch<SetStateAction<boolean>>;
  act: (action: 'start' | 'pause' | 'stop') => void | Promise<void>;
  clearLog: () => void; jobId?: string | null; speed?: number; error?: string | null;
  canStart?: boolean; projectId?: string | null; pending?: boolean;
  receipt?: Record<string, unknown> | null;
}
export interface UseEngineRunOptions {
  taskId?: string; revision?: number; enabled?: boolean;
  client?: ReturnType<typeof homeClient>; pollIntervalMs?: number;
  onCompleted?: () => void;
}
export interface EngineActionResultState { status: EngineRunStatus; jobId: string | null; message: string; error: string | null }
export function engineStatus(raw: string): EngineRunStatus {
  const states: Record<string, EngineRunStatus> = { IDLE: 'idle', QUEUED: 'queued', RUNNING: 'running', PAUSED: 'paused', COMPLETED: 'complete', CANCELLED: 'cancelled', INTERRUPTED: 'interrupted', FAILED: 'error', STOPPED: 'stopped' };
  if (!states[raw.toUpperCase()]) throw new Error('Unknown engine state.');
  return states[raw.toUpperCase()];
}
export async function executeEngineAction(
  projectId: string | null | undefined, action: 'start' | 'pause' | 'stop',
  currentStatus: EngineRunStatus, taskId?: string, client?: ReturnType<typeof homeClient>,
  revision?: number, jobId?: string | null,
): Promise<EngineActionResultState> {
  if (!projectId?.trim()) return { status: 'error', jobId: null, message: 'No active project loaded', error: 'No active project loaded' };
  try {
    const apiAction = action === 'start' && currentStatus === 'paused' ? 'resume' : action;
    const result = await (client ?? homeClient()).engineAction(projectId, apiAction, taskId, revision, jobId);
    return { status: engineStatus(result.status), jobId: result.job_id, message: `Job ${result.job_id}: ${result.status}`, error: null };
  } catch (error) { return { status: currentStatus, jobId: jobId ?? null, message: String(error), error: String(error) }; }
}
export function useEngineRun(projectId?: string | null, options: UseEngineRunOptions = {}): EngineRunHandle {
  const binding = useProjectBinding();
  const resolvedProjectId = projectId !== undefined ? projectId : binding?.state.project?.manifest.project_id;
  const taskId = options.taskId ?? binding?.state.taskId;
  const revision = options.revision ?? binding?.state.project?.revision;
  const enabled = options.enabled ?? (!!binding?.state.project && !binding.state.dirty && !binding.state.busy);
  const [status, setStatus] = useState<EngineRunStatus>('idle');
  const [step, setStep] = useState(0), [log, setLog] = useState<string[]>([]);
  const [clearOnStart, setClearOnStart] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null), [error, setError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<Record<string, unknown> | null>(null);
  const [pending, setPending] = useState(false), [refresh, setRefresh] = useState(0);
  const [recovering, setRecovering] = useState(true);
  const generation = useRef(0), acting = useRef(false), job = useRef<string | null>(null);
  const actionAbort = useRef<AbortController | null>(null);
  const callbacks = useRef(options); callbacks.current = options;
  const completed = useRef<string | null>(null);
  useEffect(() => {
    const token = ++generation.current, abort = new AbortController();
    let timer: number | undefined;
    job.current = null; completed.current = null; setPending(false); setRecovering(true);
    setJobId(null); setStatus('idle'); setStep(0); setError(null); setReceipt(null); setLog([]);
    const poll = async () => {
      if (!resolvedProjectId) return;
      try {
        const result = await (callbacks.current.client ?? homeClient({ signal: abort.signal })).getEngineStatus(resolvedProjectId, job.current);
        if (token !== generation.current || abort.signal.aborted) return;
        const next = engineStatus(result.status); setRecovering(false);
        job.current = result.job_id; setJobId(result.job_id); setStatus(next);
        setStep(Math.min(10, Math.max(0, result.progress / 10))); setReceipt(result.result ?? null);
        if (result.message) setLog(lines => lines.at(-1) === result.message ? lines : [...lines, result.message]);
        if (next === 'error' || next === 'interrupted') setError(result.message);
        if (['complete', 'cancelled', 'error', 'interrupted'].includes(next) && result.job_id && completed.current !== result.job_id) {
          completed.current = result.job_id; callbacks.current.onCompleted?.();
        }
        if (['idle', 'queued', 'running', 'paused'].includes(next)) timer = window.setTimeout(() => void poll(), callbacks.current.pollIntervalMs ?? 1000);
      } catch (failure) {
        if (token !== generation.current || abort.signal.aborted) return;
        setError(String(failure));
        timer = window.setTimeout(() => void poll(), callbacks.current.pollIntervalMs ?? 1000);
      }
    };
    void poll();
    return () => { abort.abort(); actionAbort.current?.abort(); if (timer !== undefined) window.clearTimeout(timer); generation.current++; };
  }, [resolvedProjectId, taskId, refresh]);
  const act = useCallback(async (action: 'start' | 'pause' | 'stop') => {
    if (acting.current || (action === 'start' && status !== 'paused' && (!enabled || !taskId || revision === undefined))) return;
    acting.current = true; setPending(true);
    const token = generation.current;
    if (action === 'start' && status !== 'paused' && clearOnStart) setLog([]);
    actionAbort.current = new AbortController();
    const result = await executeEngineAction(resolvedProjectId, action, status, taskId, options.client ?? homeClient({ signal: actionAbort.current.signal }), revision, job.current);
    acting.current = false;
    if (token !== generation.current) return;
    setPending(false); setStatus(result.status); setError(result.error); setJobId(result.jobId);
    job.current = result.jobId; setLog(lines => [...lines, result.message]);
    if (!result.error) setRefresh(value => value + 1);
  }, [resolvedProjectId, taskId, revision, enabled, status, clearOnStart, options.client]);
  return { status, step, log, clearOnStart, setClearOnStart, act, clearLog: () => setLog([]), jobId, error,
    projectId: resolvedProjectId, pending, receipt,
    canStart: !recovering && !pending && (status === 'paused' || (enabled && !!taskId && revision !== undefined && !['queued', 'running'].includes(status))) };
}

/** Existing local presentation state. */
export function useEnginePanel(run: EngineRunHandle) {
  const [detail, setDetail] = useState<string | null>(null);
  const [sample, setSample] = useState('Full');
  return { detail, setDetail, sample, setSample, running: run.status === 'running' };
}
