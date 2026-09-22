import { describe, expect, it } from 'vitest';

import { HEADER_APPLICATION_ACTIONS, VOLUME_PROFILE_ACTIONS } from '../../../src/app/HeaderApplications';

describe('HaruQuantAI header applications', () => {
  it('keeps the requested non-Code-Editor actions in reference order', () => {
    expect(HEADER_APPLICATION_ACTIONS.map(item => item.title)).toEqual(['Volume & Market Profile Addon', 'Debug Console', 'Grid Control']);
    expect(HEADER_APPLICATION_ACTIONS.map(item => String(item.title))).not.toContain('Code Editor');
  });

  it('uses the exact audited addon destinations', () => {
    expect(VOLUME_PROFILE_ACTIONS).toEqual(['Learn more', 'Upgrade to Ultimate', 'Pro V&MP monthly subscription', 'Pro V&MP yearly subscription']);
  });
});
