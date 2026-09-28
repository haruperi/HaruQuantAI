import type { ComponentProps } from 'react';
import { useProjectWorkbench, type WorkbenchPorts } from '../../documents';
export function ConditionalTabs(props: ComponentProps<WorkbenchPorts['ConditionalTabs']>) { const View=useProjectWorkbench().ConditionalTabs; return <View {...props}/>; }
