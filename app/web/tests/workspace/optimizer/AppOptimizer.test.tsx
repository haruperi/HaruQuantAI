import { describe, expect, it } from 'vitest';
import { OptimizerWorkspace } from '../../../workspaces/optimizer/OptimizerWorkspace';

describe('OptimizerWorkspace', () => {
  it('exports OptimizerWorkspace component', () => {
    expect(OptimizerWorkspace).toBeDefined();
    expect(typeof OptimizerWorkspace).toBe('function');
  });
});
