/** Owner-local presentation/resource documents; no backend execution authority. */
export interface CustomProject {
  id: string;
  name: string;
  description: string;
  tasks: WorkflowTask[];
  status: JobStatus;
}

export interface WorkflowTask {
  id: string;
  type: string;
  name: string;
  enabled: boolean;
  status: JobStatus;
  input: string;
  output: string;
  config?: Record<string, any>;
  durationSeconds?: number;
  errorPolicy?: 'Stop project' | 'Continue to next' | 'Go to task';
  goToTaskId?: string;
  progress?: number;
}

export type JobStatus = 'idle' | 'queued' | 'running' | 'paused' | 'cancelled' | 'failed' | 'completed';
