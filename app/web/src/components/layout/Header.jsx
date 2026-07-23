import React, { useState, useEffect } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import {
  ChevronLeft,
  Plus,
  Info,
  MoreVertical,
  Star,
  Copy,
  Pencil,
  Trash2,
  Check,
  FileJson
} from 'lucide-react';

export const Header = () => {
  const {
    practiceBalance,
    challengeBalance,
    netPL,
    margin,
    available,
    mode,
    oneClickTrading,
    toggleOneClickTrading,
    workspaces,
    activeWorkspaceId,
    setActiveWorkspace,
    addWorkspace,
    defaultWorkspaceId,
    setDefaultWorkspace,
    renameWorkspace,
    duplicateWorkspace,
    deleteWorkspace
  } = useTradingStore();

  const [currentTime, setCurrentTime] = useState('');
  const [workspaceMenuId, setWorkspaceMenuId] = useState(null);
  const [renameWorkspaceId, setRenameWorkspaceId] = useState(null);
  const [renameDraft, setRenameDraft] = useState('');
  const [workspaceToast, setWorkspaceToast] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const timeStr = now.toLocaleTimeString('en-US', { hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' }).toLowerCase() + ' CDT 07/21/2026';
      setCurrentTime(timeStr);
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const isChallenge = mode === 'challenge';
  const displayFunds = isChallenge ? challengeBalance : practiceBalance;

  const showWorkspaceToast = (message) => {
    setWorkspaceToast(message);
    window.setTimeout(() => setWorkspaceToast(''), 1800);
  };

  const openRename = (workspace) => {
    setRenameWorkspaceId(workspace.id);
    setRenameDraft(workspace.name);
    setWorkspaceMenuId(null);
  };

  const commitRename = (workspaceId) => {
    renameWorkspace(workspaceId, renameDraft);
    setRenameWorkspaceId(null);
    showWorkspaceToast('Workspace renamed');
  };

  const copyWorkspaceJson = async (workspace) => {
    const payload = JSON.stringify(workspace, null, 2);
    try {
      await navigator.clipboard.writeText(payload);
      showWorkspaceToast('Workspace JSON copied');
    } catch {
      showWorkspaceToast('Copy unavailable');
    }
    setWorkspaceMenuId(null);
  };

  const handleAddWorkspace = () => {
    if (workspaces.length >= 10) {
      showWorkspaceToast('Maximum 10 workspaces allowed');
      return;
    }
    addWorkspace();
    showWorkspaceToast('New Workspace created');
  };

  const handleDuplicateWorkspace = (wsId) => {
    if (workspaces.length >= 10) {
      showWorkspaceToast('Maximum 10 workspaces allowed');
      setWorkspaceMenuId(null);
      return;
    }
    duplicateWorkspace(wsId);
    setWorkspaceMenuId(null);
    showWorkspaceToast('Workspace duplicated');
  };

  return (
    <div className="header-container-stack">
      {/* 1. TOP HEADER BAR matching reference image */}
      <header className="cme-header-top">
        {/* Brand CME Group Logo */}
        <div className="cme-logo-area">
          <div className="cme-brand-badge">
            <span style={{ color: '#fff', fontWeight: 900, fontSize: '13px', letterSpacing: '-0.5px' }}>CME</span>
          </div>
          <span className="cme-brand-title">CME Group</span>
        </div>

        {/* Financial Metrics Status Bar */}
        <div className="account-metrics-bar">
          <div className="metric-item">
            <span className="metric-label">{isChallenge ? 'CHALLENGE FUNDS' : 'PRACTICE FUNDS'}</span>
            <span className="metric-value neutral">${displayFunds.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
          </div>

          <div className="metric-item">
            <span className="metric-label">PROFIT/LOSS</span>
            <span className={`metric-value ${netPL > 0 ? 'positive' : netPL < 0 ? 'negative' : 'neutral'}`}>
              {netPL < 0 ? `-$${Math.abs(netPL).toFixed(2)}` : `$${netPL.toFixed(2)}`}
            </span>
          </div>

          <div className="metric-item">
            <span className="metric-label">MARGIN</span>
            <span className="metric-value neutral">${margin.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
          </div>

          <div className="metric-item">
            <span className="metric-label">AVAILABLE</span>
            <span className="metric-value neutral">${available.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
          </div>

          <button className="cme-metric-caret" title="Collapse metrics">
            <ChevronLeft size={14} />
          </button>
        </div>

        {/* Right Info, 1-Click Toggle & Profile Badge */}
        <div className="cme-header-actions">
          <span className="cme-clock-text">
            {currentTime}
          </span>

          {/* 1-Click Toggle Pill (to the left of username) */}
          <div
            className={`one-click-toggle ${oneClickTrading ? 'active-one-click' : ''}`}
            onClick={() => {
              toggleOneClickTrading();
              showWorkspaceToast(!oneClickTrading ? '⚡ 1-Click Trading ENABLED' : '1-Click Trading DISABLED');
            }}
            title={oneClickTrading ? '1-Click Trading ON (Immediate Order Execution)' : '1-Click Trading OFF (Shows Order Confirmation)'}
          >
            <div className={`cme-toggle-switch ${oneClickTrading ? 'active' : ''}`}>
              <div className="cme-toggle-knob" />
            </div>
            <span style={{ fontWeight: oneClickTrading ? 700 : 500, color: oneClickTrading ? '#00e473' : 'inherit' }}>1-Click</span>
            <Info size={12} color={oneClickTrading ? "#00e473" : "#8a99ad"} />
          </div>

          {/* User Profile Avatar & Name */}
          <div className="cme-user-badge">
            <div className="cme-avatar-circle">R</div>
            <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
              <span className="cme-user-name">Rufaro Haruperi</span>
              <span className="cme-user-sub">Practice Mode</span>
            </div>
          </div>

          {/* Far Right Rating Badge (★ 2.0) */}
          <div className="cme-orange-badge">
            <Star size={12} fill="#fff" color="#fff" />
            <span>2.0</span>
          </div>
        </div>
      </header>

      {/* 2. SUB HEADER WORKSPACE TABS BAR matching reference image */}
      <div className="cme-header-sub">
        {/* Workspace Sub-Tabs List */}
        <div className="workspace-tabs-row">
          {workspaces.map((ws) => (
            <div
              key={ws.id}
              className={`workspace-sub-tab ${ws.id == activeWorkspaceId ? 'active' : ''} ${workspaceMenuId === ws.id ? 'menu-open' : ''}`}
              onClick={() => setActiveWorkspace(ws.id)}
            >
              <Star size={12} fill={ws.id == activeWorkspaceId ? "#0088cc" : "transparent"} color={ws.id == activeWorkspaceId ? "#0088cc" : "#6b7c93"} />
              <span>{ws.name}</span>
              <MoreVertical
                size={13}
                className="tab-menu-icon"
                title={`Workspace menu: ${ws.name}`}
                onClick={(event) => { event.stopPropagation(); setWorkspaceMenuId(workspaceMenuId === ws.id ? null : ws.id); setRenameWorkspaceId(null); }}
              />

              {workspaceMenuId === ws.id && (
                <div className="workspace-action-menu" onClick={(event) => event.stopPropagation()}>
                  <button onClick={() => handleDuplicateWorkspace(ws.id)}>
                    <Copy size={15} /><span>Duplicate</span>
                  </button>
                  <button onClick={() => { setDefaultWorkspace(ws.id); setWorkspaceMenuId(null); showWorkspaceToast('Default workspace updated'); }}>
                    {defaultWorkspaceId == ws.id ? <Check size={15} color="#3cc8ff" /> : <Star size={15} />}<span>Set as Default</span>
                  </button>
                  <button onClick={() => openRename(ws)}>
                    <Pencil size={15} /><span>Rename Workspace</span>
                  </button>
                  <button onClick={() => copyWorkspaceJson(ws)}>
                    <FileJson size={15} /><span>Copy Workspace JSON</span>
                  </button>
                  <div className="workspace-menu-divider" />
                  <button className="danger" onClick={() => { deleteWorkspace(ws.id); setWorkspaceMenuId(null); showWorkspaceToast(workspaces.length > 1 ? 'Workspace deleted' : 'Keep at least one workspace'); }}>
                    <Trash2 size={15} /><span>Delete</span>
                  </button>
                </div>
              )}

              {renameWorkspaceId === ws.id && (
                <div className="workspace-rename-popover" onClick={(event) => event.stopPropagation()}>
                  <label htmlFor={`workspace-name-${ws.id}`}>Rename Workspace</label>
                  <input
                    id={`workspace-name-${ws.id}`}
                    value={renameDraft}
                    onChange={(event) => setRenameDraft(event.target.value)}
                    onKeyDown={(event) => { if (event.key === 'Enter') commitRename(ws.id); if (event.key === 'Escape') setRenameWorkspaceId(null); }}
                    autoFocus
                  />
                  <div className="workspace-rename-actions">
                    <button onClick={() => setRenameWorkspaceId(null)}>Cancel</button>
                    <button className="primary" onClick={() => commitRename(ws.id)}>Save</button>
                  </div>
                </div>
              )}
            </div>
          ))}

          <div
            className={`add-workspace-sub-btn ${workspaces.length >= 10 ? 'disabled' : ''}`}
            onClick={handleAddWorkspace}
            title={workspaces.length >= 10 ? "Maximum 10 Workspaces Allowed" : "Create New Workspace"}
          >
            <Plus size={14} />
          </div>
        </div>
        {workspaceToast && <div className="workspace-action-toast" role="status">{workspaceToast}</div>}
      </div>
    </div>
  );
};
