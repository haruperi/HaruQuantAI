import { describe, expect, it } from 'vitest';
import { SettingsBlocks } from '../../../workspaces/builder/SettingsBlocks';

describe('SettingsBlocks', () => {
  it('exports SettingsBlocks component properly', () => {
    expect(SettingsBlocks).toBeDefined();
    expect(typeof SettingsBlocks).toBe('function');
  });
});
