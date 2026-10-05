import type { ComponentProps } from 'react';
import { useProjectWorkbench, type WorkbenchPorts } from '../../documents';
export function SpOverviewTab(props: ComponentProps<WorkbenchPorts['SpOverviewTab']>) { const View=useProjectWorkbench().SpOverviewTab; return <View {...props}/>; }
export function TradeAnalysisTab(props: ComponentProps<WorkbenchPorts['TradeAnalysisTab']>) { const View=useProjectWorkbench().TradeAnalysisTab; return <View {...props}/>; }
export function ProfileChartTab(props: ComponentProps<WorkbenchPorts['ProfileChartTab']>) { const View=useProjectWorkbench().ProfileChartTab; return <View {...props}/>; }
export function StrategyConfigTab(props: ComponentProps<WorkbenchPorts['StrategyConfigTab']>) { const View=useProjectWorkbench().StrategyConfigTab; return <View {...props}/>; }
export function CustomAnalysisTab(props: ComponentProps<WorkbenchPorts['CustomAnalysisTab']>) { const View=useProjectWorkbench().CustomAnalysisTab; return <View {...props}/>; }
