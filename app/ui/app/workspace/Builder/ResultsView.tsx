import type { ComponentProps } from 'react';
import { useProjectWorkbench, type WorkbenchPorts } from './documents';
export function ResultsView(props: ComponentProps<WorkbenchPorts['ProjectResults']>) { const View=useProjectWorkbench().ProjectResults; return <View {...props}/>; }
