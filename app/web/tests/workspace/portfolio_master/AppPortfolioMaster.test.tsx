import { describe, expect, it } from 'vitest';
import { PortfolioMasterWorkspace } from '../../../workspaces/portfolio_master/PortfolioMasterWorkspace';

describe('AppPortfolioMaster Component', () => {
  it('exports PortfolioMasterWorkspace component properly', () => {
    expect(PortfolioMasterWorkspace).toBeDefined();
    expect(typeof PortfolioMasterWorkspace).toBe('function');
  });
});
