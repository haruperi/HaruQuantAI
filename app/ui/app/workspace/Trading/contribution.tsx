import type { UIContribution } from '../../host/contributions';
import { Activity } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.trading', kind:'workspace', version:'1.0.0', slots:[],
navigation: { id:'trading', path:'/trading', aliases:[], label:"Live Trading", icon:Activity, order:14, hidden:false, home:false },
load: async () => ({ View: (await import('./TradingDashboard')).TradingDashboard }),
};
