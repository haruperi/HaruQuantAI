'use client';

import React, { useState, useEffect } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import {
  useWorkspaceStore,
  ACCOUNT_MODE_SETTING_KEY,
  isSelectableAccountMode,
  type SelectableAccountMode,
  type Workspace,
} from '../../features/workspaces';
import { useAuth } from '../../context';
import { ProfileDropdown } from './ProfileDropdown';
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
import { apiClients, unwrapData, type TradingAccountProfile } from '@/clients';
import {
  clockSegmentsAtOffset,
  localClockSegments,
  localOffsetMinutes,
  parseUtcOffset,
  type ClockSegments,
} from './clock';

/**
 * What each mode means, stated plainly on hover.
 *
 * Demo and live are technically one path into the same MT5 terminal and are
 * separated by the credentials the operator configured, so the tooltip says
 * exactly that rather than implying demo is a safety mechanism.
 */
const ACCOUNT_MODE_TITLES: Record<string, string> = {
  sim: 'SIM: orders are executed virtually by the simulator. Nothing reaches a broker.',
  demo: 'DEMO: orders are sent to the connected MT5 terminal using the demo credentials you configured.',
  live: 'LIVE: orders are sent to the connected MT5 terminal using the live credentials you configured. Real money.',
  unknown: 'Account mode has not been resolved yet - order entry is disabled.',
};

export const Header: React.FC = () => {
  const {
    practiceBalance,
    challengeBalance,
    netPL,
    margin,
    available,
    mode,
    openSettings
  } = useTradingStore();
  const { logout } = useAuth();

  const {
    orderConfirmationRequired,
    setOrderConfirmationRequired,
    accountMode,
    accountModeVersion,
    applyAccountMode,
    workspaces,
    activeWorkspaceId,
    setActiveWorkspace,
    addWorkspace,
    defaultWorkspaceId,
    setDefaultWorkspace,
    renameWorkspace,
    duplicateWorkspace,
    deleteWorkspace
  } = useWorkspaceStore();

  const [profileMenuOpen, setProfileMenuOpen] = useState(false);

  const [clock, setClock] = useState<ClockSegments | null>(null);
  const [timeMismatch, setTimeMismatch] = useState(false);
  const [workspaceMenuId, setWorkspaceMenuId] = useState<number | null>(null);
  const [renameWorkspaceId, setRenameWorkspaceId] = useState<number | null>(null);
  const [renameDraft, setRenameDraft] = useState('');
  const [workspaceToast, setWorkspaceToast] = useState('');

  // Configured display timezone from the TIMEZONE system setting. Held in
  // state so the clock effect can recompute without refetching each tick.
  // Null/undefined means "use device-local time" (the safe fallback when the
  // setting is absent, unparseable, or the backend is unreachable).
  const [tzValue, setTzValue] = useState<string | undefined>(undefined);
  const [tzLoaded, setTzLoaded] = useState(false);

  // The whole system-settings document, held so a mode change can be written
  // back as the complete document the backend's replace semantics expect.
  // Writing only ACCOUNT_MODE would erase every other setting.
  const [systemSettings, setSystemSettings] = useState<Record<string, string> | null>(null);
  const [accountModePending, setAccountModePending] = useState(false);
  const [accountProfile, setAccountProfile] = useState<TradingAccountProfile | null>(null);
  const [accountProfileLoading, setAccountProfileLoading] = useState(false);

  const accountName = accountProfile?.account_name
    ?? (accountProfileLoading ? 'Account loading' : 'Account unavailable');
  const accountEnvironment = accountProfile?.environment_label
    ?? (accountProfileLoading ? 'Environment loading' : 'Environment unavailable');
  const avatarLetter = accountName.charAt(0).toUpperCase() || 'A';

  useEffect(() => {
    if (tzLoaded) return;
    let cancelled = false;
    void apiClients.settings
      .readSystem()
      .then((response) => {
        if (cancelled) return;
        const current = unwrapData(response);
        setTzValue(current.settings.TIMEZONE);
        setSystemSettings(current.settings);
        // The record version is recorded even when no mode is stored yet: it
        // is what the first-ever selection needs to lock its write against.
        // Until an operator has chosen, the mode the session reported stands.
        const stored = current.settings[ACCOUNT_MODE_SETTING_KEY];
        applyAccountMode(
          isSelectableAccountMode(stored)
            ? stored
            : useWorkspaceStore.getState().accountMode,
          current.version,
        );
      })
      .catch(() => {
        // Auth failure or backend unreachable: fall back to local time and
        // leave the account mode as the session reported it.
        if (!cancelled) setTzValue(undefined);
      })
      .finally(() => {
        if (!cancelled) setTzLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, [tzLoaded, applyAccountMode]);

  useEffect(() => {
    if (accountMode === 'unknown' || accountModePending) {
      setAccountProfile(null);
      return;
    }
    let cancelled = false;
    setAccountProfileLoading(true);
    void apiClients.trading
      .accountProfile()
      .then((response) => {
        if (!cancelled) setAccountProfile(unwrapData(response));
      })
      .catch(() => {
        if (!cancelled) setAccountProfile(null);
      })
      .finally(() => {
        if (!cancelled) setAccountProfileLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [accountMode, accountModeVersion, accountModePending]);

  /**
   * Persist an operator-selected account mode as the app-wide context.
   *
   * The mode is applied optimistically so the shell recolours immediately, and
   * reverted if the write is refused - the application must never present a
   * mode the backend is not actually routing to.
   */
  const handleSelectAccountMode = (mode: SelectableAccountMode) => {
    if (mode === accountMode || accountModePending) return;
    if (systemSettings === null || accountModeVersion < 0) {
      showWorkspaceToast('Account mode unavailable - settings not loaded');
      return;
    }
    const previousMode = accountMode;
    const previousVersion = accountModeVersion;
    setAccountModePending(true);
    applyAccountMode(mode, previousVersion);
    void apiClients.settings
      .updateSystem(
        { ...systemSettings, [ACCOUNT_MODE_SETTING_KEY]: mode },
        previousVersion,
      )
      .then((response) => {
        const updated = unwrapData(response);
        setSystemSettings(updated.settings);
        applyAccountMode(mode, updated.version);
        showWorkspaceToast(`Account mode: ${mode.toUpperCase()}`);
      })
      .catch(() => {
        applyAccountMode(previousMode === 'unknown' ? 'sim' : previousMode, previousVersion);
        showWorkspaceToast('Account mode change refused');
      })
      .finally(() => setAccountModePending(false));
  };

  useEffect(() => {
    const updateTime = () => {
      const parsed = parseUtcOffset(tzValue);
      if (parsed === null) {
        // No valid configured offset: render device-local time and never flag
        // a mismatch (there is nothing to compare against).
        const label = tzValue && tzValue.trim() ? tzValue : `UTC${localOffsetMinutes() / 60 >= 0 ? '+' : ''}${localOffsetMinutes() / 60}`;
        setClock(localClockSegments(label));
        setTimeMismatch(false);
        return;
      }
      const local = localOffsetMinutes();
      setClock(clockSegmentsAtOffset(Date.now(), parsed, tzValue as string));
      setTimeMismatch(parsed !== local);
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, [tzValue]);

  const isChallenge = mode === 'challenge';
  const displayFunds = isChallenge ? challengeBalance : practiceBalance;

  const showWorkspaceToast = (message: string) => {
    setWorkspaceToast(message);
    window.setTimeout(() => setWorkspaceToast(''), 1800);
  };

  const openRename = (workspace: Workspace) => {
    setRenameWorkspaceId(workspace.id);
    setRenameDraft(workspace.name);
    setWorkspaceMenuId(null);
  };

  const commitRename = (workspaceId: number) => {
    renameWorkspace(workspaceId, renameDraft);
    setRenameWorkspaceId(null);
    showWorkspaceToast('Workspace renamed');
  };

  const copyWorkspaceJson = async (workspace: Workspace) => {
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

  const handleDuplicateWorkspace = (wsId: number) => {
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
        {/* Brand HaruQuantAI Logo */}
        <div className="cme-logo-area">
          <div className="cme-brand-badge">
            <span style={{ color: '#fff', fontWeight: 900, fontSize: '13px', letterSpacing: '-0.5px' }}>HQ</span>
          </div>
          <span className="cme-brand-title">HaruQuantAI</span>
        </div>

        {/* Financial Metrics Status Bar */}
        <div className="account-metrics-bar">
          {/* Account mode badge (FR-UI-016/205): the app-wide mode, always
              visible and colour-coded to match the profile dropdown. */}
          <span
            className="metric-item account-mode-badge"
            role="status"
            data-mode={accountMode}
            title={ACCOUNT_MODE_TITLES[accountMode]}
          >
            {accountMode === 'unknown' ? 'MODE UNKNOWN' : accountMode.toUpperCase()}
          </span>

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

        {/* Right Info, Confirmation-Mode Toggle & Profile Badge */}
        <div className="cme-header-actions">
          <div
            className={`digital-time${timeMismatch ? ' mismatch' : ''}`}
            aria-label={clock ? `${clock.hour}:${clock.minute}:${clock.second} ${clock.meridiem} ${clock.label} ${clock.date}` : 'clock'}
          >
            {clock && (
              <>
                <span className="dt-seg">{clock.hour}</span>
                <span className="dt-colon" aria-hidden="true">:</span>
                <span className="dt-seg">{clock.minute}</span>
                <span className="dt-colon" aria-hidden="true">:</span>
                <span className="dt-seg">{clock.second}</span>
                <span className="dt-suffix">{` ${clock.meridiem} ${clock.label} ${clock.date}`}</span>
              </>
            )}
          </div>

          {/* Order-confirmation mode toggle (FR-UI-011/013), always visible.
              Checked means 1-click trading: orders submit with no dialog. */}
          <div
            className="one-click-toggle"
            role="switch"
            aria-checked={!orderConfirmationRequired}
            aria-label="1-Click trading"
            tabIndex={0}
            onClick={() => {
              setOrderConfirmationRequired(!orderConfirmationRequired);
              showWorkspaceToast(orderConfirmationRequired ? '⚡ Order confirmation DISABLED' : 'Order confirmation ENABLED');
            }}
            onKeyDown={(event: React.KeyboardEvent) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                setOrderConfirmationRequired(!orderConfirmationRequired);
                showWorkspaceToast(orderConfirmationRequired ? '⚡ Order confirmation DISABLED' : 'Order confirmation ENABLED');
              }
            }}
            title={orderConfirmationRequired ? 'Order confirmation ON (every order shows a confirmation dialog)' : 'Order confirmation OFF (orders submit immediately)'}
          >
            <div className={`cme-toggle-switch ${!orderConfirmationRequired ? 'active' : ''}`}>
              <div className="cme-toggle-knob" />
            </div>
            <span className="one-click-label">1-Click</span>
            <span
              className="one-click-info"
              title="1-click trading enables users to execute a trade with a single click without displaying a secondary confirmation of the trade. Order submissions are based on settings and selections the user configures prior to execution."
            >
              <Info size={12} aria-hidden="true" />
            </span>
          </div>

          {/* User Profile Avatar & Name with dropdown chevron */}
          <div className="cme-user-badge">
            <div className="cme-avatar-circle">{avatarLetter}</div>
            <div className="cme-user-text">
              <div className="cme-user-top">
                <span className="cme-user-name">{accountName}</span>
                <button
                  type="button"
                  className="profile-dropdown-button"
                  aria-haspopup="menu"
                  aria-expanded={profileMenuOpen}
                  aria-label={profileMenuOpen ? 'Close profile menu' : 'Open profile menu'}
                  onClick={() => setProfileMenuOpen(!profileMenuOpen)}
                >
                  <ChevronLeft size={14} />
                </button>
              </div>
              <span className="cme-user-sub">{accountEnvironment}</span>
            </div>
            <ProfileDropdown
              open={profileMenuOpen}
              onClose={() => setProfileMenuOpen(false)}
              accountMode={accountMode}
              pending={accountModePending}
              onSelectAccountMode={handleSelectAccountMode}
              onOpenSettings={() => openSettings()}
              onLogout={() => {
                void logout().then(
                  () => showWorkspaceToast('Signed out'),
                  () => showWorkspaceToast('Sign out failed'),
                );
              }}
            />
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
              // eslint-disable-next-line eqeqeq -- workspace id is number; caller may pass string
              className={`workspace-sub-tab ${ws.id == activeWorkspaceId ? 'active' : ''} ${workspaceMenuId === ws.id ? 'menu-open' : ''}`}
              onClick={() => setActiveWorkspace(ws.id)}
            >
              {/* eslint-disable-next-line eqeqeq -- workspace id is number; caller may pass string */}
              <Star size={12} fill={ws.id == activeWorkspaceId ? "#0088cc" : "transparent"} color={ws.id == activeWorkspaceId ? "#0088cc" : "#6b7c93"} />
              <span>{ws.name}</span>
              <span title={`Workspace menu: ${ws.name}`} style={{ display: 'inline-flex' }}>
                <MoreVertical
                  size={13}
                  className="tab-menu-icon"
                  onClick={(event: React.MouseEvent) => { event.stopPropagation(); setWorkspaceMenuId(workspaceMenuId === ws.id ? null : ws.id); setRenameWorkspaceId(null); }}
                />
              </span>

              {workspaceMenuId === ws.id && (
                <div className="workspace-action-menu" onClick={(event: React.MouseEvent) => event.stopPropagation()}>
                  <button onClick={() => handleDuplicateWorkspace(ws.id)}>
                    <Copy size={15} /><span>Duplicate</span>
                  </button>
                  <button onClick={() => { setDefaultWorkspace(ws.id); setWorkspaceMenuId(null); showWorkspaceToast('Default workspace updated'); }}>
                    {/* eslint-disable-next-line eqeqeq -- workspace id is number; caller may pass string */}
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
                <div className="workspace-rename-popover" onClick={(event: React.MouseEvent) => event.stopPropagation()}>
                  <label htmlFor={`workspace-name-${ws.id}`}>Rename Workspace</label>
                  <input
                    id={`workspace-name-${ws.id}`}
                    value={renameDraft}
                    onChange={(event: React.ChangeEvent<HTMLInputElement>) => setRenameDraft(event.target.value)}
                    onKeyDown={(event: React.KeyboardEvent<HTMLInputElement>) => { if (event.key === 'Enter') commitRename(ws.id); if (event.key === 'Escape') setRenameWorkspaceId(null); }}
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
