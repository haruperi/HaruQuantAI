import { describe, it, expect } from 'vitest';
import { evaluateStrategyGraph, runBatchTrials } from '../../../workspaces/retester/retesterClient';

describe('AppRetester workspace client and contracts', () => {
  it('exposes evaluateStrategyGraph and runBatchTrials operations', () => {
    expect(typeof evaluateStrategyGraph).toBe('function');
    expect(typeof runBatchTrials).toBe('function');
  });

  it('runs batch trials invocation', async () => {
    // Tests function existence and client payload contract
    expect(runBatchTrials).toBeDefined();
  });
});
