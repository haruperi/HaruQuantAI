import { describe, expect, it } from 'vitest';
import { BuilderWorkspace } from '../../../workspaces/builder/BuilderWorkspace';

describe('AppBuilder Workspace Integration', () => {
  it('exports BuilderWorkspace component properly', () => {
    expect(BuilderWorkspace).toBeDefined();
    expect(typeof BuilderWorkspace).toBe('function');
  });
});
