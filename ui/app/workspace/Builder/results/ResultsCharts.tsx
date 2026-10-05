import type { ComponentProps } from 'react';
import { useProjectWorkbench, type WorkbenchPorts } from '../documents';
export function ResultsChart(props: ComponentProps<WorkbenchPorts['ResultsChart']>) { const View=useProjectWorkbench().ResultsChart; return <View {...props}/>; }
export function TradesChart() { const View=useProjectWorkbench().TradesChart; return <View/>; }
