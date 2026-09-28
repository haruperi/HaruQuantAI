import type { UIContribution } from '../../host/contributions';
import { Square } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.debug_console', kind:'workspace', version:'1.0.0', slots:[],
navigation: { id:'debugconsole', path:'/debugconsole', aliases:[], label:"DebugConsole", icon:Square, order:100, hidden:true, home:false },
load: async () => ({ View: (await import('./DebugConsoleWorkspace')).DebugConsoleWorkspace }),
};
