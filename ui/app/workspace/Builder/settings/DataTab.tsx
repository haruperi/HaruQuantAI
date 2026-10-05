import type { ComponentProps } from 'react';
import { useProjectWorkbench, type WorkbenchPorts } from '../documents';
export function DataTab(props: ComponentProps<WorkbenchPorts['DataTab']>) { const View=useProjectWorkbench().DataTab; return <View {...props}/>; }
