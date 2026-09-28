import type { UIContribution } from '../../host/contributions';
import { BriefcaseBusiness } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.business', kind:'workspace', version:'1.0.0', slots:[],
navigation: { id:'business', path:'/business', aliases:[], label:"Business", icon:BriefcaseBusiness, order:3, hidden:false, home:false },
load: async () => ({ View: (await import('./BusinessWorkspace')).BusinessWorkspace }),
};
