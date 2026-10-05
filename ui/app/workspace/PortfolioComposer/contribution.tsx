import type { UIContribution } from '../../host/contributions';
import { ChartNoAxesCombined } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.portfolio_composer', kind:'workspace', requires:['project.workbench'], version:'1.0.0', slots:["project.workbench"],
navigation: { id:'composer', path:'/composer', aliases:[], label:"Portfolio Composer", icon:ChartNoAxesCombined, order:13, hidden:false, home:false },
load: async () => ({ View: (await import('./PortfolioComposerWorkspace')).PortfolioComposerWorkspace }),
};
