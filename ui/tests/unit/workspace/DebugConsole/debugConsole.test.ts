import { describe, expect, it } from 'vitest';

import { debugCategories, deriveDebugLog, filterDebugLog } from '../../../../app/workspace/DebugConsole/DebugConsoleWorkspace';
import type { Job } from '../../../../app/host/types';

const job = (status: Job['status'], progress: number, message: string = status): Job => ({ id: `job-${status}`, kind: 'Research', status, progress, accepted: 0, rejected: 0, startedAt: '2026-09-20T12:30:00', message });

describe('HaruQuantAI debug console workspace', () => {
  it('derives, categorizes, filters and bounds safe debug entries', () => {
    const entries = deriveDebugLog({ builder: job('running', 37, 'Generating candidates') }, ['Saved configuration']);
    expect(debugCategories(entries)).toEqual(['All', 'Jobs', 'Application', 'System', 'Engine']);
    expect(filterDebugLog(entries, 'Jobs', 'candidates')).toHaveLength(1);
    expect(filterDebugLog(entries, 'Application', 'CANDIDATES')).toHaveLength(0);
    const large = deriveDebugLog({}, Array.from({ length: 200 }, (_, index) => `${index}-${'x'.repeat(100)}`));
    expect(large.reduce((sum, entry) => sum + `${entry.time} ${entry.category} - ${entry.message}`.length, 0)).toBeLessThanOrEqual(10_000);
  });
});
