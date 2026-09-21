import { describe, expect, it } from 'vitest';

import { HEADER_APPLICATION_ACTIONS, VOLUME_PROFILE_ACTIONS, classifyGridJobs, debugCategories, deriveDebugLog, filterDebugLog } from './HeaderApplications';
import type { Job } from './types';

const job = (status: Job['status'], progress: number, message: string = status): Job => ({ id: `job-${status}`, kind: 'Research', status, progress, accepted: 0, rejected: 0, startedAt: '2026-09-20T12:30:00', message });

describe('HaruQuantAI header applications', () => {
  it('keeps the requested non-Code-Editor actions in reference order', () => {
    expect(HEADER_APPLICATION_ACTIONS.map(item => item.title)).toEqual(['Volume & Market Profile Addon', 'Debug Console', 'Grid Control']);
    expect(HEADER_APPLICATION_ACTIONS.map(item => String(item.title))).not.toContain('Code Editor');
  });

  it('derives, categorizes, filters and bounds safe debug entries', () => {
    const entries = deriveDebugLog({ builder: job('running', 37, 'Generating candidates') }, ['Saved configuration']);
    expect(debugCategories(entries)).toEqual(['All', 'Jobs', 'Application', 'System', 'Engine']);
    expect(filterDebugLog(entries, 'Jobs', 'candidates')).toHaveLength(1);
    expect(filterDebugLog(entries, 'Application', 'CANDIDATES')).toHaveLength(0);
    const large = deriveDebugLog({}, Array.from({ length: 200 }, (_, index) => `${index}-${'x'.repeat(100)}`));
    expect(large.reduce((sum, entry) => sum + `${entry.time} ${entry.category} - ${entry.message}`.length, 0)).toBeLessThanOrEqual(10_000);
  });

  it('classifies live jobs and includes bounded deterministic finished history', () => {
    const sections = classifyGridJobs({ running: job('running', 50), queued: job('queued', 0), failed: job('failed', 42, 'Validation failed') });
    expect(sections.running.map(item => item.id)).toEqual(['job-running']);
    expect(sections.waiting.map(item => item.id)).toEqual(['job-queued']);
    expect(sections.finished[0]).toMatchObject({ id: 'job-failed', status: 'Error', error: 'Validation failed' });
    expect(sections.finished).toHaveLength(3);
    expect(sections.finished.length).toBeLessThanOrEqual(100);
  });

  it('uses the exact audited addon destinations', () => {
    expect(VOLUME_PROFILE_ACTIONS).toEqual(['Learn more', 'Upgrade to Ultimate', 'Pro V&MP monthly subscription', 'Pro V&MP yearly subscription']);
  });
});
