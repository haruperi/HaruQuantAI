import { describe, expect, it } from 'vitest';
import { PortfolioComposer } from '../../../workspaces/portfolio_composer/PortfolioComposer';

describe('PortfolioComposer Component', () => {
  it('exports PortfolioComposer component properly', () => {
    expect(PortfolioComposer).toBeDefined();
    expect(typeof PortfolioComposer).toBe('object');
  });
});
