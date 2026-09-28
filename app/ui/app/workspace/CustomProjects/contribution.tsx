import type { UIContribution } from '../../host/contributions';
import { FolderKanban } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.custom_projects', kind:'workspace', version:'1.0.0', slots:["databank.panel"],
navigation: { tabs: ['progress','settings','results'], defaultTab: 'progress', id:'projects', path:'/projects', aliases:[], label:"Custom Projects", icon:FolderKanban, order:11, hidden:false, home:false, group:"Automation" },
load: async () => ({ View: (await import('./CustomProjectsWorkspace')).CustomProjectsWorkspace }),
};
