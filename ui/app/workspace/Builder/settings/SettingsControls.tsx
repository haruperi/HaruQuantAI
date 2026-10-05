import type { ComponentProps } from 'react';
import { useProjectWorkbench, type WorkbenchPorts } from '../documents';
export function SqdFieldset(props: ComponentProps<WorkbenchPorts['SqdFieldset']>) { const View=useProjectWorkbench().SqdFieldset; return <View {...props}/>; }
export function SqdRadio(props: ComponentProps<WorkbenchPorts['SqdRadio']>) { const View=useProjectWorkbench().SqdRadio; return <View {...props}/>; }
export function SqdSpinner(props: ComponentProps<WorkbenchPorts['SqdSpinner']>) { const View=useProjectWorkbench().SqdSpinner; return <View {...props}/>; }
export function SqdSlider(props: ComponentProps<WorkbenchPorts['SqdSlider']>) { const View=useProjectWorkbench().SqdSlider; return <View {...props}/>; }
export function SqdCheckbox(props: ComponentProps<WorkbenchPorts['SqdCheckbox']>) { const View=useProjectWorkbench().SqdCheckbox; return <View {...props}/>; }
export function SqdSelect(props: ComponentProps<WorkbenchPorts['SqdSelect']>) { const View=useProjectWorkbench().SqdSelect; return <View {...props}/>; }
export function SqdTextInput(props: ComponentProps<WorkbenchPorts['SqdTextInput']>) { const View=useProjectWorkbench().SqdTextInput; return <View {...props}/>; }
export function SqdHelpLink(props: ComponentProps<WorkbenchPorts['SqdHelpLink']>) { const View=useProjectWorkbench().SqdHelpLink; return <View {...props}/>; }
export function GearLink(props: ComponentProps<WorkbenchPorts['GearLink']>) { const View=useProjectWorkbench().GearLink; return <View {...props}/>; }
export function AdditionalConfigPopup(props: ComponentProps<WorkbenchPorts['AdditionalConfigPopup']>) { const View=useProjectWorkbench().AdditionalConfigPopup; return <View {...props}/>; }
export function useOpenState(...args: Parameters<WorkbenchPorts['useOpenState']>) { return useProjectWorkbench().useOpenState(...args); }
