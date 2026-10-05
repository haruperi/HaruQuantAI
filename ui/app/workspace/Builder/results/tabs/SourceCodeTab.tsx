import type { ComponentProps } from 'react';
import { useProjectWorkbench, type WorkbenchPorts } from '../../documents';
export function SourceCodeTab(props: ComponentProps<WorkbenchPorts['SourceCodeTab']>) { const View=useProjectWorkbench().SourceCodeTab; return <View {...props}/>; }
