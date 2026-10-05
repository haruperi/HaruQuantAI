import type { UIContribution } from '../../host/contributions';
import { Layers3 } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.portfolio_master', kind:'workspace', requires:['project.workbench'], version:'1.0.0', slots:["project.workbench","databank.panel"],
navigation: { tabs: ['progress','settings','results'], defaultTab: 'progress', id:'portfolio', path:'/portfolio', aliases:[], label:"Portfolio Master", icon:Layers3, order:12, hidden:false, home:false, group:"Trading" },
load: async () => ({ View: (await import('./PortfolioMasterWorkspace')).PortfolioMasterWorkspace }),
};
