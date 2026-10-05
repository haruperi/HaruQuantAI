import type { UIContribution } from '../../host/contributions';
import { WandSparkles } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.builder', kind:'workspace', requires:['project.workbench'], version:'1.0.0', slots:["project.workbench","databank.panel"],
navigation: { tabs: ['progress','settings','results'], defaultTab: 'progress', id:'builder', path:'/builder', aliases:[], label:"Builder", icon:WandSparkles, order:4, hidden:false, home:false, group:"Development" },
load: async () => ({ View: (await import('./BuilderWorkspace')).BuilderWorkspace }),
};
