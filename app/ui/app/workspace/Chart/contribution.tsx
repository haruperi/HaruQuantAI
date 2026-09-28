import type { UIContribution } from '../../host/contributions';
import { LineChart } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.chart', kind:'workspace', version:'1.0.0', slots:[],
navigation: { id:'chart', path:'/chart', aliases:[], label:"Chart", icon:LineChart, order:2, hidden:false, home:false },
load: async () => ({ View: (await import('./ChartWorkspace')).ChartWorkspace }),
};
