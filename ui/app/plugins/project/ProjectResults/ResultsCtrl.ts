import { useState } from 'react';
import type { ResultSection } from '../ProjectWorkbench/contracts';
import type { ResultDocument } from '../ProjectWorkbench/results/resultsModel';
import { builtInResultTabs, defaultCustomAnalysisTabs, hiddenUntilResultTabs, orderResultTabs } from '../ProjectWorkbench/results/resultsFixtures';

/** Existing session-only results selection and analysis lifecycle. */
export function useProjectResults(result: ResultDocument | null, extraSections: ResultSection[], visibleTabIds?: readonly string[]) {
    const [activeId, setActiveId] = useState<string>('overview');
    const [customTabs, setCustomTabs] = useState<string[]>(defaultCustomAnalysisTabs);
    const [newOpen, setNewOpen] = useState(false);
    const [renameTarget, setRenameTarget] = useState<string | null>(null);
    const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
    const [menuFor, setMenuFor] = useState<string | null>(null);
    const [resetKey, setResetKey] = useState(0);
    const standard = [...builtInResultTabs, ...hiddenUntilResultTabs.filter(tab => result && (tab.id !== 'tradesOnChart' || result.chartData) && (tab.id !== 'stockpicker' || result.stockpicker))];
    const available = [...standard.filter(tab=>!visibleTabIds||visibleTabIds.includes(tab.id)),...extraSections];
    const tabs = orderResultTabs(available, customTabs);
    const active = tabs.find(t => t.id === activeId) ?? tabs[0];
    const onReload = () => {
        setActiveId('overview');
        setMenuFor(null);
        setResetKey(k => k + 1);
    };
    const onCreate = (name: string) => {
        setCustomTabs(t => [...t, name]);
        setNewOpen(false);
        setActiveId(`custom:${name}`);
    };
    const onRename = (name: string) => {
        if (renameTarget == null)
            return;
        setCustomTabs(t => t.map(n => (n === renameTarget ? name : n)));
        if (activeId === `custom:${renameTarget}`)
            setActiveId(`custom:${name}`);
        setRenameTarget(null);
    };
    const onDelete = () => {
        if (deleteTarget == null)
            return;
        setCustomTabs(t => t.filter(n => n !== deleteTarget));
        if (activeId === `custom:${deleteTarget}`)
            setActiveId('overview');
        setDeleteTarget(null);
    };
    return { activeId, setActiveId, customTabs, newOpen, setNewOpen, renameTarget, setRenameTarget, deleteTarget, setDeleteTarget, menuFor, setMenuFor, resetKey, tabs, active, onReload, onCreate, onRename, onDelete };
}
