import { describe, expect, it } from 'vitest';
import { strategies } from '../../../workspaces/results/databank/fixtures';
import { portfolioMembers } from '../../../workspaces/portfolio_composer/fixtures';

describe('portfolio composer fixtures', () => {
  it('uses stable strategy IDs for portfolio membership', () => {
    const ids = new Set(strategies.map(s => s.id));
    expect(portfolioMembers.length).toBeGreaterThan(0);
    expect(portfolioMembers.every(member => ids.has(member.strategyId))).toBe(true);
  });
});
