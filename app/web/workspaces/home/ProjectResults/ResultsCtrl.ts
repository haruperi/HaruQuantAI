import { useEffect, useState } from 'react';
import { useProjectBinding } from '../projectController';
import type { ResultSection } from '../../../common/project/contracts';
import type { ResultDocument } from '../../../common/project/results/resultsModel';
import { builtInResultTabs, defaultCustomAnalysisTabs, hiddenUntilResultTabs, orderResultTabs } from '../../../common/project/results/resultsFixtures';

/** Existing session-only results selection and analysis lifecycle. */
export function useProjectResults(result: ResultDocument | null, extraSections: ResultSection[], visibleTabIds?: readonly string[]) {
    const binding = useProjectBinding();
    const [activeId, setActiveId] = useState<string>('overview');
    const [customTabs, setCustomTabs] = useState<string[]>(binding ? [] : defaultCustomAnalysisTabs);
    const [newOpen, setNewOpen] = useState(false);
    const [renameTarget, setRenameTarget] = useState<string | null>(null);
    const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
    const [menuFor, setMenuFor] = useState<string | null>(null);
    const [resetKey, setResetKey] = useState(0);
    const standard = [...builtInResultTabs, ...hiddenUntilResultTabs.filter(tab => result && (tab.id !== 'tradesOnChart' || result.chartData) && (tab.id !== 'stockpicker' || result.stockpicker))];
    const available = [...standard.filter(tab=>!visibleTabIds||visibleTabIds.includes(tab.id)),...extraSections];
    const tabs = orderResultTabs(available, customTabs);
    const active = tabs.find(t => t.id === activeId) ?? tabs[0] ?? { id: 'overview', title: 'Overview', position: 0 };
    useEffect(() => {
        if (!binding) return;
        const names = binding.state.project?.metadata?.analysis_tabs;
        setCustomTabs(Array.isArray(names) ? names.filter((name): name is string => typeof name === 'string') : []);
        setActiveId('overview');
    }, [binding?.state.project?.manifest.project_id, binding?.state.project?.metadata?.analysis_tabs]);
    const persist = async (names: string[]) => {
        if (binding && !await binding.controller.saveAnalysis(names)) return false;
        setCustomTabs(names); return true;
    };
    const onReload = () => { setActiveId('overview'); setMenuFor(null); setResetKey(k => k + 1); void binding?.controller.refreshResults(); };
    const onCreate = async (name: string) => {
        if (!await persist([...customTabs, name])) return;
        setNewOpen(false); setActiveId(`custom:${name}`);
    };
    const onRename = async (name: string) => {
        if (renameTarget == null || !await persist(customTabs.map(old => old === renameTarget ? name : old))) return;
        if (activeId === `custom:${renameTarget}`) setActiveId(`custom:${name}`);
        setRenameTarget(null);
    };
    const onDelete = async () => {
        if (deleteTarget == null || !await persist(customTabs.filter(name => name !== deleteTarget))) return;
        if (activeId === `custom:${deleteTarget}`) setActiveId('overview');
        setDeleteTarget(null);
    };
    return { activeId, setActiveId, customTabs, newOpen, setNewOpen, renameTarget, setRenameTarget, deleteTarget, setDeleteTarget, menuFor, setMenuFor, resetKey, tabs, active, onReload, onCreate, onRename, onDelete };
}
