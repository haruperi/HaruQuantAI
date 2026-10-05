import type { ComponentProps } from 'react';
import { useProjectWorkbench, type WorkbenchPorts } from '../documents';
export function NewAnalysisModal(props: ComponentProps<WorkbenchPorts['NewAnalysisModal']>) { const View=useProjectWorkbench().NewAnalysisModal; return <View {...props}/>; }
export function RenameAnalysisModal(props: ComponentProps<WorkbenchPorts['RenameAnalysisModal']>) { const View=useProjectWorkbench().RenameAnalysisModal; return <View {...props}/>; }
export function DeleteAnalysisModal(props: ComponentProps<WorkbenchPorts['DeleteAnalysisModal']>) { const View=useProjectWorkbench().DeleteAnalysisModal; return <View {...props}/>; }
export function ManageViewsModal(props: ComponentProps<WorkbenchPorts['ManageViewsModal']>) { const View=useProjectWorkbench().ManageViewsModal; return <View {...props}/>; }
export function ExportTradesModal(props: ComponentProps<WorkbenchPorts['ExportTradesModal']>) { const View=useProjectWorkbench().ExportTradesModal; return <View {...props}/>; }
export function ModalLinks(props: ComponentProps<WorkbenchPorts['ModalLinks']>) { const View=useProjectWorkbench().ModalLinks; return <View {...props}/>; }
