import type { ReactNode } from 'react';

export type ProjectPanel = 'progress' | 'settings' | 'results';
export type RunStatus = 'idle' | 'running' | 'paused' | 'complete';
export interface SettingsSection {
  id: string;
  title: string;
  help: string;
  helpUrl: string;
  content: ReactNode;
}
export interface ResultSection {
  id: string;
  title: string;
  position: number;
  content: ReactNode;
}

/** Local preview lifecycle only. Never submits a quantitative job. */
export function nextRunStatus(status: RunStatus, action: 'start' | 'pause' | 'stop' | 'complete'): RunStatus {
  if (action === 'stop') return 'idle';
  if (action === 'pause') return status === 'running' ? 'paused' : status;
  if (action === 'complete') return status === 'running' ? 'complete' : status;
  return 'running';
}
