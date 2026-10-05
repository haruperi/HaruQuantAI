import type { UIContribution } from '../../host/contributions';
import { Database } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.data_manager', kind:'workspace', version:'1.0.0', slots:["data_source.presentation", "data_source.acquisition"],
navigation: { id:'datamanager', path:'/datamanager', aliases:[], label:"Data Manager", icon:Database, order:1, hidden:false, home:false, group:"Fundamentals" },
load: async () => ({ View: (await import('./DataManager')).DataManager }),
};
