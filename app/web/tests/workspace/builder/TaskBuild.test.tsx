import { describe, expect, it } from 'vitest';
import { TaskBuild } from '../../../workspaces/builder/TaskBuild';

describe('TaskBuild', () => {
  it('exports TaskBuild component properly', () => {
    expect(TaskBuild).toBeDefined();
    expect(typeof TaskBuild).toBe('function');
  });
});
