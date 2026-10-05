import type { UIContribution } from '../../host/contributions';
import { Square } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.grid_test', kind:'workspace', version:'1.0.0', slots:[],
navigation: { id:'gridtest', path:'/gridtest', aliases:[], label:"GridTest", icon:Square, order:100, hidden:true, home:false },
load: async () => ({ View: (await import('./GridTestWorkspace')).GridTestWorkspace }),
};
