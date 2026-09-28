import type { UIContribution } from '../../host/contributions';
import { GitCompareArrows } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.retester', kind:'workspace', requires:['project.workbench'], version:'1.0.0', slots:["project.workbench","databank.panel"],
navigation: { tabs: ['progress','settings','results'], defaultTab: 'progress', id:'retester', path:'/retester', aliases:[], label:"Retester", icon:GitCompareArrows, order:8, hidden:false, home:false, group:"Robustness" },
load: async () => ({ View: (await import('./RetesterWorkspace')).RetesterWorkspace }),
};
