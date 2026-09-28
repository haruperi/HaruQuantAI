import type { ComponentProps } from 'react';
import { useProjectWorkbench, type WorkbenchPorts } from '../documents';
export function NotesTab() { const View=useProjectWorkbench().NotesTab; return <View/>; }
