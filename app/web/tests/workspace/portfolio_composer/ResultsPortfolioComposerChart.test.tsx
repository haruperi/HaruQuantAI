import { describe, expect, it } from 'vitest';
import { ResultsPortfolioComposerChart } from '../../../workspaces/portfolio_composer/ResultsPortfolioComposerChart';

describe('ResultsPortfolioComposerChart Component', () => {
  it('exports ResultsPortfolioComposerChart component properly', () => {
    expect(ResultsPortfolioComposerChart).toBeDefined();
    expect(typeof ResultsPortfolioComposerChart).toBe('object');
  });
});
