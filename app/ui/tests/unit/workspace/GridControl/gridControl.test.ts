import { describe, expect, it } from 'vitest';

import { classifyGridJobs } from '../../../../app/workspace/GridControl/GridControlWorkspace';
import type { Job } from '../../../../app/workspace/GridControl/documents';

const job = (status: Job['status'], progress: number, message: string = status): Job => ({ id: `job-${status}`, kind: 'Research', status, progress, accepted: 0, rejected: 0, startedAt: '2026-09-20T12:30:00', message });

describe('HaruQuantAI grid control workspace', () => {
  it('classifies live jobs and includes bounded deterministic finished history', () => {
    const sections = classifyGridJobs({ running: job('running', 50), queued: job('queued', 0), failed: job('failed', 42, 'Validation failed') });
    expect(sections.running.map(item => item.id)).toEqual(['job-running']);
    expect(sections.waiting.map(item => item.id)).toEqual(['job-queued']);
    expect(sections.finished[0]).toMatchObject({ id: 'job-failed', status: 'Error', error: 'Validation failed' });
    expect(sections.finished).toHaveLength(3);
    expect(sections.finished.length).toBeLessThanOrEqual(100);
  });
});
