import type { UIContribution } from '../../host/contributions';
import { Gauge } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.optimizer', kind:'workspace', requires:['project.workbench'], version:'1.0.0', slots:["project.workbench","databank.panel"],
navigation: { tabs: ['progress','settings','results'], defaultTab: 'progress', id:'optimizer', path:'/optimizer', aliases:[], label:"Optimizer", icon:Gauge, order:9, hidden:false, home:false },
load: async () => ({ View: (await import('./OptimizerWorkspace')).OptimizerWorkspace }),
};
