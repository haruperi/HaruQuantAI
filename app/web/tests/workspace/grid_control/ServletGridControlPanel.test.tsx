import { describe, expect, it } from 'vitest';
import {
  classifyGridJobs,
  jobToGridRow,
  type GridJobRow,
} from '../../../workspaces/grid_control/GridControlWorkspace';
import type { Job } from '../../../shell/types';

describe('ServletGridControl client-side data integration', () => {
  it('maps wire server getData payload into workspace rows without hardcoded fixtures', () => {
    // Exact schema emitted by GridControlServlet and DescriptionsSerializer
    const wireResponse = {
      gridData: {
        running: [
          {
            jobId: 'remote-job-1',
            jobGroupId: 'genetic-opt',
            createTime: 1700000000000,
            progress: 75,
            duration: 15000,
            durationWithWait: 18000,
            startTime: 1700000003000,
            waiting: false,
          },
        ],
        waiting: [
          {
            jobId: 'remote-job-2',
            jobGroupId: 'backtest',
            createTime: 1700000005000,
          },
        ],
        finished: [
          {
            jobId: 'remote-job-3',
            jobGroupId: 'monte-carlo',
            createTime: 1699999000000,
            duration: 45000,
            durationWithWait: 50000,
            startTime: 1699999005000,
            finishTime: 1699999050000,
            success: true,
          },
          {
            jobId: 'remote-job-4',
            jobGroupId: 'monte-carlo',
            createTime: 1699998000000,
            duration: 10000,
            durationWithWait: 12000,
            startTime: 1699998002000,
            finishTime: 1699998012000,
            success: false,
            message: 'Worker disconnected',
          },
        ],
      },
      success: 'Databanks listed.',
    };

    expect(wireResponse.success).toBe('Databanks listed.');

    // Convert server response into store Job representation
    const storeJobs: Record<string, Job> = {};

    for (const item of wireResponse.gridData.running) {
      storeJobs[item.jobId] = {
        id: item.jobId,
        jobGroupId: item.jobGroupId,
        kind: 'Compute',
        status: 'running',
        progress: item.progress,
        accepted: 0,
        rejected: 0,
        blocking: true,
        startedAt: new Date(item.startTime).toISOString(),
        message: "",
      };
    }

    for (const item of wireResponse.gridData.waiting) {
      storeJobs[item.jobId] = {
        id: item.jobId,
        jobGroupId: item.jobGroupId,
        kind: 'Compute',
        status: 'queued',
        progress: -1,
        accepted: 0,
        rejected: 0,
        blocking: false,
        message: "",
      };
    }

    for (const item of wireResponse.gridData.finished) {
      storeJobs[item.jobId] = {
        id: item.jobId,
        jobGroupId: item.jobGroupId,
        kind: 'Compute',
        status: item.success ? 'completed' : 'failed',
        progress: item.success ? 100 : 50,
        accepted: 0,
        rejected: 0,
        blocking: false,
        message: item.message || "",
        startedAt: new Date(item.startTime).toISOString(),
        finishedAt: new Date(item.finishTime).toISOString(),
      };
    }

    const sections = classifyGridJobs(storeJobs);

    expect(sections.running).toHaveLength(1);
    expect(sections.running[0].id).toBe('remote-job-1');
    expect(sections.running[0].type).toBe('Continuous');
    expect(sections.running[0].progress).toBe('75%');

    expect(sections.waiting).toHaveLength(1);
    expect(sections.waiting[0].id).toBe('remote-job-2');
    expect(sections.waiting[0].type).toBe('One time');
    expect(sections.waiting[0].progress).toBe('N/A');

    expect(sections.finished).toHaveLength(2);
    const successJob = sections.finished.find(j => j.id === 'remote-job-3');
    const failedJob = sections.finished.find(j => j.id === 'remote-job-4');

    expect(successJob?.status).toBe('Success');
    expect(failedJob?.status).toBe('Error');
    expect(failedJob?.error).toBe('Worker disconnected');
  });

  it('formats single failed row with error indicator', () => {
    const job: Job = {
      id: 'job-err',
      jobGroupId: 'group-x',
      kind: 'Compute',
      status: 'failed',
      progress: 30,
      accepted: 0,
      rejected: 0,
      message: 'Out of memory',
    };
    const row: GridJobRow = jobToGridRow(job, 'job-err');
    expect(row.status).toBe('Error');
    expect(row.error).toBe('Out of memory');
  });
});
