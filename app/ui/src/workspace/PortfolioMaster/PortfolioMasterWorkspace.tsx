import { PortfolioWorkspace } from '../PortfolioComposer/PortfolioComposerWorkspace';

export function PortfolioMasterWorkspace() {
  return <PortfolioWorkspace master={true} />;
}
export { PortfolioMasterWorkspace as PortfolioMaster };
