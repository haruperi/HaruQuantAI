import { describe, expect, it } from 'vitest';

import { classifyGridJobs, jobToGridRow } from '../../../workspaces/grid_control/GridControlWorkspace';
import type { Job } from '../../../shell/types';

const makeJob = (
  id: string,
  status: Job['status'],
  progress: number,
  blocking: boolean = false,
  message: string = "",
): Job => ({
  id,
  jobGroupId: 'grid-group-1',
  kind: 'Research',
  status,
  progress,
  accepted: 0,
  rejected: 0,
  blocking,
  startedAt: '2026-09-20T12:30:00',
  message,
});

describe('HaruQuantAI grid control workspace classification', () => {
  it('classifies live jobs without hardcoded mock fixtures', () => {
    const jobs: Record<string, Job> = {
      running: makeJob('job-running', 'running', 50, true),
      queued: makeJob('job-queued', 'queued', -1, false),
      failed: makeJob('job-failed', 'failed', 42.5, false, 'Validation failed'),
      completed: makeJob('job-completed', 'completed', 100, true),
    };

    const sections = classifyGridJobs(jobs);

    expect(sections.running.map(item => item.id)).toEqual(['job-running']);
    expect(sections.running[0].type).toBe('Continuous');
    expect(sections.running[0].progress).toBe('50%');

    expect(sections.waiting.map(item => item.id)).toEqual(['job-queued']);
    expect(sections.waiting[0].type).toBe('One time');
    expect(sections.waiting[0].progress).toBe('N/A');

    expect(sections.finished).toHaveLength(2);
    expect(sections.finished.map(item => item.id)).toContain('job-failed');
    expect(sections.finished.map(item => item.id)).toContain('job-completed');

    const failedRow = sections.finished.find(item => item.id === 'job-failed');
    expect(failedRow).toMatchObject({
      id: 'job-failed',
      status: 'Error',
      error: 'Validation failed',
      progress: '42.5%',
    });
  });

  it('converts single job to grid row with donor presentation logic', () => {
    const job = makeJob('test-1', 'running', 12.5, false);
    const row = jobToGridRow(job, 'test-1');
    expect(row.type).toBe('One time');
    expect(row.progress).toBe('12.5%');
    expect(row.status).toBe('Running');
  });
});
