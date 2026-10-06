import { useState } from 'react';
export const optionalColumns = ['Open time', 'Close time', 'Open price', 'Close price'] as const;

/** Existing session-only view drafts, kept alive even when the modal is closed. */
export function useTradelistViews() {
    const [views, setViews] = useState<Record<string, string[]>>({ Default: [...optionalColumns] });
    const [view, setView] = useState('Default');
    const [name, setName] = useState('');
    const [columns, setColumns] = useState<string[]>([...optionalColumns]);
    const [manage, setManage] = useState(false);
    const visible = views[view];
    const save = () => { const key = name.trim(); setViews(v => ({ ...v, [key]: columns })); setView(key); setName(''); };
    return { views, setViews, view, setView, name, setName, columns, setColumns, manage, setManage, visible, save };
}
