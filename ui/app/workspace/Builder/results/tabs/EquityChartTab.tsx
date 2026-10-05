import type { ComponentProps } from 'react';
import { useProjectWorkbench, type WorkbenchPorts } from '../../documents';
export function EquityChartTab(props: ComponentProps<WorkbenchPorts['EquityChartTab']>) { const View=useProjectWorkbench().EquityChartTab; return <View {...props}/>; }
