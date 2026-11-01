import { describe, expect, it } from 'vitest';
import { SettingsRankings } from '../../../workspaces/builder/SettingsRankings';

describe('SettingsRankings', () => {
  it('exports SettingsRankings component properly', () => {
    expect(SettingsRankings).toBeDefined();
    expect(typeof SettingsRankings).toBe('function');
  });
});
