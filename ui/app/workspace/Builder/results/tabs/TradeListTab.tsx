import type { ComponentProps } from 'react';
import { useProjectWorkbench, type WorkbenchPorts } from '../../documents';
export function TradeListTab(props: ComponentProps<WorkbenchPorts['TradeListTab']>) { const View=useProjectWorkbench().TradeListTab; return <View {...props}/>; }
