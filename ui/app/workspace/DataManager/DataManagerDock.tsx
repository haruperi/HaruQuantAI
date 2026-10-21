import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { DockviewReact, type DockviewApi, type DockviewReadyEvent, type IDockviewPanelProps } from 'dockview';
import type { WorkspaceLayout, WorkspaceTabId } from './dataManagerWorkspaceClient';
import './DataManagerDock.css';

export type WorkspaceArrangement = 'right' | 'bottom' | 'main' | 'close';
export interface WorkspaceArrangeRequest { seq: number; action: WorkspaceArrangement; targetId?: WorkspaceTabId }

const PanelContent = createContext<(id: WorkspaceTabId) => ReactNode>(() => null);
function WorkspacePanel({ api }: IDockviewPanelProps) {
  const render = useContext(PanelContent);
  return <div className="dm-dock-panel" data-workspace-panel={api.id}>{render(api.id as WorkspaceTabId)}</div>;
}
const components = { workspace: WorkspacePanel };

export function DataManagerDock({ layout, activeId, activation, chartRequest, arrangeRequest = null, onActivate, renderPanel }: {
  layout: WorkspaceLayout; activeId: WorkspaceTabId; activation: number; chartRequest: number;
  arrangeRequest?: WorkspaceArrangeRequest | null;
  onActivate: (id: WorkspaceTabId) => void; renderPanel: (id: WorkspaceTabId) => ReactNode;
}) {
  const dock = useRef<DockviewApi | null>(null);
  const callback = useRef(onActivate);
  callback.current = onActivate;
  const subscriptions = useRef<Array<{ dispose(): void }>>([]);
  const [openPanels, setOpenPanels] = useState('');
  const syncPanels = () => setOpenPanels((dock.current?.panels ?? []).map(panel => panel.id).join(','));

  function open(id: WorkspaceTabId, split = false) {
    const api = dock.current;
    if (!api) return;
    const existing = api.getPanel(id);
    if (existing) { if (!split) existing.api.setActive(); return; }
    const description = layout.tabs.find(tab => tab.id === id);
    if (!description) return;
    const splitRight = split || id === 'chart';
    const reference = api.getPanel('data') ?? api.panels[0];
    api.addPanel({ id, component: 'workspace', title: description.title,
      ...(reference ? { position: { referencePanel: reference.id, direction: splitRight ? 'right' : 'within' } } : {}),
      ...(splitRight ? { initialWidth: Math.max(400, api.width * 0.4) } : {}),
    });
    if (split) reference?.api.setActive();
  }

  const onReady = (event: DockviewReadyEvent) => {
    dock.current = event.api;
    for (const group of event.api.groups) group.header.hidden = true;
    subscriptions.current = [
      event.api.onDidAddGroup(group => { group.header.hidden = true; }),
      event.api.onDidAddPanel(syncPanels),
      event.api.onDidRemovePanel(syncPanels),
      event.api.onDidActivePanelChange(panel => { if (panel) callback.current(panel.id as WorkspaceTabId); }),
    ];
    for (const tab of layout.tabs.filter(item => item.core)) open(tab.id);
    syncPanels();
    event.api.getPanel(layout.active_tab)?.api.setActive();
  };
  useEffect(() => { open(activeId); }, [activeId, activation]);
  useEffect(() => { if (chartRequest) open('chart', true); }, [chartRequest]);
  useEffect(() => {
    const api = dock.current;
    if (!api || !arrangeRequest) return;
    const panel = api.getPanel(arrangeRequest.targetId ?? activeId) ?? api.activePanel;
    if (!panel) return;
    if (arrangeRequest.action === 'close') {
      panel.api.close();
      const next = (api.getPanel('data') ?? api.panels[0])?.id as WorkspaceTabId | undefined;
      if (next) { api.getPanel(next)?.api.setActive(); callback.current(next); }
      return;
    }
    const mainGroup = api.getPanel('data')?.group ?? api.groups.find(group => group !== panel.group) ?? api.groups[0];
    if (!mainGroup) return;
    if (arrangeRequest.action === 'main') {
      if (panel.group !== mainGroup) panel.api.moveTo({ group: mainGroup, position: 'center' });
      panel.api.setActive();
      return;
    }
    const referenceGroup = panel.group.size > 1 ? panel.group : mainGroup;
    if (referenceGroup === panel.group && panel.group.size < 2) return;
    panel.api.moveTo({ group: referenceGroup, position: arrangeRequest.action });
    panel.api.setActive();
  }, [arrangeRequest]);
  useEffect(() => () => { subscriptions.current.forEach(item => item.dispose()); subscriptions.current = []; dock.current = null; }, []);

  return <PanelContent.Provider value={renderPanel}>
    <div className="dm-dock-host dockview-theme-dark" aria-label="Data Manager dockable workspace" data-open-panels={openPanels}>
      <DockviewReact components={components} onReady={onReady} disableFloatingGroups />
    </div>
  </PanelContent.Provider>;
}
