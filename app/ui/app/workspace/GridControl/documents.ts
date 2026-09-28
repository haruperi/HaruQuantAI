/** Owner-local presentation/resource documents; no backend execution authority. */
export interface Job {
  id: string;
  kind: string;
  status: JobStatus;
  progress: number;
  accepted: number;
  rejected: number;
  startedAt?: string;
  message: string;
}

export type JobStatus = 'idle' | 'queued' | 'running' | 'paused' | 'cancelled' | 'failed' | 'completed';
