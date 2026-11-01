import { describe, expect, it } from 'vitest';
import { PortfolioComposerWorkspace } from '../../../workspaces/portfolio_composer/PortfolioComposerWorkspace';

describe('AppPortfolioComposer Workspace Integration', () => {
  it('exports PortfolioComposerWorkspace component properly', () => {
    expect(PortfolioComposerWorkspace).toBeDefined();
    expect(typeof PortfolioComposerWorkspace).toBe('function');
  });
});
