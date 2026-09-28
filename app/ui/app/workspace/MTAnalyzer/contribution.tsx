import type { UIContribution } from '../../host/contributions';
import { LineChart } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.m_t_analyzer', kind:'workspace', version:'1.0.0', slots:[],
navigation: { id:'mtanalyzer', path:'/mtanalyzer', aliases:[], label:"MT Analyzer", icon:LineChart, order:10, hidden:false, home:false },
load: async () => ({ View: (await import('./MTAnalyzerWorkspace')).MTAnalyzerWorkspace }),
};
