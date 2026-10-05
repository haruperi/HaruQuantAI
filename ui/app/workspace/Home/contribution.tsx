import type { UIContribution } from '../../host/contributions';
import { ChartNoAxesCombined } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.home', kind:'workspace', version:'1.0.0', slots:[],
navigation: { id:'home', path:'/', aliases:["/home"], label:"HaruQuantAI", icon:ChartNoAxesCombined, order:0, hidden:false, home:true },
load: async () => ({ View: (await import('./HomeScreen')).HomeScreen }),
};
