import type { UIContribution } from '../../host/contributions';
import { Workflow } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.algo_wizard', kind:'workspace', version:'1.0.0', slots:[],
navigation: { id:'algowizard', path:'/algowizard', aliases:[], label:"AlgoWizard", icon:Workflow, order:5, hidden:false, home:false },
load: async () => ({ View: (await import('./AlgoWizardWorkspace')).AlgoWizardWorkspace }),
};
