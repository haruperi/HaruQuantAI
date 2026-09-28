import { describe, expect, it } from 'vitest';
import { useAppStore } from '../../../../app/workspace/PortfolioComposer/localState';
const strategies = useAppStore.getState().strategies;
import { portfolioMembers } from '../../../../app/workspace/PortfolioComposer/fixtures';

describe('portfolio composer fixtures', () => {
  it('uses stable strategy IDs for portfolio membership', () => {
    const ids = new Set(strategies.map(s => s.id));
    expect(portfolioMembers.length).toBeGreaterThan(0);
    expect(portfolioMembers.every(member => ids.has(member.strategyId))).toBe(true);
  });
});
