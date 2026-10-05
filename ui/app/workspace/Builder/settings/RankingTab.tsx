import type { ComponentProps } from 'react';
import { useProjectWorkbench, type WorkbenchPorts } from '../documents';
export function RankingTab(props: ComponentProps<WorkbenchPorts['RankingTab']>) { const View=useProjectWorkbench().RankingTab; return <View {...props}/>; }
