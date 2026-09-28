import type { UIContribution } from '../../host/contributions';
import { Code2 } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.code_editor', kind:'workspace', version:'1.0.0', slots:[],
navigation: { id:'codeeditor', path:'/codeeditor', aliases:[], label:"Code Editor", icon:Code2, order:6, hidden:false, home:false },
load: async () => ({ View: (await import('./CodeEditorWorkspace')).CodeEditorWorkspace }),
};
