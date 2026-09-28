import type { ComponentProps } from 'react';
import { useProjectWorkbench, type WorkbenchPorts } from '../../documents';
export function OverviewTab(props: ComponentProps<WorkbenchPorts['OverviewTab']>) { const View=useProjectWorkbench().OverviewTab; return <View {...props}/>; }
