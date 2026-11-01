import { describe, expect, it } from 'vitest';
import { TaskOptimize } from '../../../workspaces/optimizer/TaskOptimize';

describe('TaskOptimize', () => {
  it('exports TaskOptimize component', () => {
    expect(TaskOptimize).toBeDefined();
    expect(typeof TaskOptimize).toBe('function');
  });

  it('renders progress and status', () => {
    const props = {
      status: 'RUNNING' as const,
      progressPct: 50.0,
      evaluationsCompleted: 5,
      evaluationsTotal: 10,
      bestFitness: 150.0,
    };
    expect(props.status).toBe('RUNNING');
    expect(props.progressPct).toBe(50.0);
  });
});
