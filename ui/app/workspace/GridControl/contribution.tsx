import type { UIContribution } from '../../host/contributions';
import { Square } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.grid_control', kind:'workspace', version:'1.0.0', slots:[],
navigation: { id:'gridcontrol', path:'/gridcontrol', aliases:[], label:"GridControl", icon:Square, order:100, hidden:true, home:false },
load: async () => ({ View: (await import('./GridControlWorkspace')).GridControlWorkspace }),
};
