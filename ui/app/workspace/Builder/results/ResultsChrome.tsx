import type { ComponentProps } from 'react';
import { useProjectWorkbench, type WorkbenchPorts } from '../documents';
export function SqrDropdown(props: ComponentProps<WorkbenchPorts['SqrDropdown']>) { const View=useProjectWorkbench().SqrDropdown; return <View {...props}/>; }
export function SegmentedButtons(props: ComponentProps<WorkbenchPorts['SegmentedButtons']>) { const View=useProjectWorkbench().SegmentedButtons; return <View {...props}/>; }
export function ResultsToolbar(props: ComponentProps<WorkbenchPorts['ResultsToolbar']>) { const View=useProjectWorkbench().ResultsToolbar; return <View {...props}/>; }
