'use client';

import React, { useState, useEffect } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import {
  useWorkspaceStore,
  ACCOUNT_MODE_SETTING_KEY,
  isSelectableAccountMode,
  type SelectableAccountMode,
  type Workspace,
} from '../../widgets/workspaces';
import { useAuth } from '../../context';
import { ProfileDropdown } from './ProfileDropdown';
import { AccountMetricsMenu } from './AccountMetricsMenu';
import { TimeCorrectionDialog, type TimeCorrection } from './TimeCorrectionDialog';
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

/** Bound how long UI compatibility evidence can remain unrefreshed. */
const ACCOUNT_PROFILE_REFRESH_MS = 5_000;

const metricNumber = (value: string | number | null | undefined): number | null => {
  if (value === null || value === undefined) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const formatMoney = (value: string | number | null | undefined, currency?: string | null): string => {
  const parsed = metricNumber(value);
  if (parsed === null) return '—';
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
      minimumFractionDigits: 2,
    }).format(parsed);
  } catch {
    return parsed.toLocaleString('en-US', { minimumFractionDigits: 2 });
  }
};

const formatProfitPercent = (
  profit: string | number | null | undefined,
  balance: string | number | null | undefined,
): string => {
  const parsedProfit = metricNumber(profit);
  const parsedBalance = metricNumber(balance);
  if (parsedProfit === null || parsedBalance === null || parsedBalance === 0) return '—';
  return `${((parsedProfit / parsedBalance) * 100).toFixed(2)}%`;
};

export const Header: React.FC = () => {
  const { openSettings } = useTradingStore();
  const { logout } = useAuth();

  const {
    orderConfirmationRequired,
    setOrderConfirmationRequired,
    accountMode,
    accountModeVersion,
    applyAccountMode,
    platformAccountMode,
    tradingModeCompatible,
    applyPlatformAccountMode,
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
  const [metricsMenuOpen, setMetricsMenuOpen] = useState(false);
  const [profitDisplay, setProfitDisplay] = useState<'money' | 'percent'>('money');

  const [clock, setClock] = useState<ClockSegments | null>(null);
  const [timeMismatch, setTimeMismatch] = useState(false);
  const [timeCorrectionOpen, setTimeCorrectionOpen] = useState(false);
  const [clockCorrectionMs, setClockCorrectionMs] = useState(0);
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
  const sessionName = accountProfileLoading
    ? 'LOADING'
    : (accountProfile?.session_name ?? 'NO SESSION');
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
      applyPlatformAccountMode('unknown', false);
      return;
    }
    let cancelled = false;
    const refreshProfile = (): void => {
      setAccountProfileLoading(true);
      void apiClients.trading.accountProfile().then((response) => {
        if (!cancelled) {
          const profile = unwrapData(response);
          const platformMode = profile.trade_mode === 'SIMULATION'
            ? 'sim'
            : profile.trade_mode === 'DEMO'
              ? 'demo'
              : profile.trade_mode === 'REAL'
                ? 'live'
                : 'contest';
          setAccountProfile(profile);
          applyPlatformAccountMode(platformMode, profile.mode_compatible);
        }
      }).catch(() => {
        if (!cancelled) {
          setAccountProfile(null);
          applyPlatformAccountMode('unknown', false);
        }
      }).finally(() => {
        if (!cancelled) setAccountProfileLoading(false);
      });
    };

    // Automatically start the session named "Default" (or is_default session) for the active mode on load if no session is running.
    void apiClients.trading.listExecutionSessions?.()
      .then(async (response) => {
        if (cancelled || !response) return;
        const sessions = unwrapData(response);
        const active = sessions.find((s) => s.is_active && s.lifecycle_state === 'running');
        if (!active) {
          const target = sessions.find(
            (s) => s.mode === accountMode && (s.name.toLowerCase() === 'default' || s.is_default)
          );
          if (target && target.lifecycle_state !== 'running') {
            await apiClients.trading.actOnExecutionSession?.('start', target);
            if (!cancelled) refreshProfile();
          }
        }
      })
      .catch(() => {
        // Non-fatal if session registry is unavailable
      });

    refreshProfile();
    const timer = window.setInterval(refreshProfile, ACCOUNT_PROFILE_REFRESH_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [accountMode, accountModeVersion, accountModePending, applyPlatformAccountMode]);

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
      .then(async (response) => {
        const updated = unwrapData(response);
        setSystemSettings(updated.settings);
        applyAccountMode(mode, updated.version);
        showWorkspaceToast(`Account mode: ${mode.toUpperCase()}`);

        // Coordinate session transition: stop former session if mode changed and start new mode's default session
        try {
          const sessionsRes = await apiClients.trading.listExecutionSessions?.();
          if (sessionsRes) {
            const sessions = unwrapData(sessionsRes);
            const active = sessions.find((s) => s.is_active);
            if (active && active.mode !== mode) {
              await apiClients.trading.actOnExecutionSession?.('stop', active);
            }
            const target = sessions.find(
              (s) => s.mode === mode && (s.name.toLowerCase() === 'default' || s.is_default)
            );
            if (target && target.lifecycle_state !== 'running') {
              await apiClients.trading.actOnExecutionSession?.('start', target);
            }
          }
        } catch {
          // Non-fatal if session transition fails
        }
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
      setClock(clockSegmentsAtOffset(Date.now() + clockCorrectionMs, parsed, tzValue as string));
      setTimeMismatch(parsed !== local);
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, [tzValue, clockCorrectionMs]);

  const persistClockTimezone = async (timezone: string): Promise<boolean> => {
    if (systemSettings === null || accountModeVersion < 0) return false;
    try {
      const updated = unwrapData(await apiClients.settings.updateSystem(
        { ...systemSettings, TIMEZONE: timezone },
        accountModeVersion,
      ));
      setSystemSettings(updated.settings);
      applyAccountMode(accountMode, updated.version);
      setTzValue(timezone);
      return true;
    } catch {
      return false;
    }
  };

  const handleApplyTimeCorrection = async (correction: TimeCorrection): Promise<boolean> => {
    if (!await persistClockTimezone(correction.timezone)) return false;
    setClockCorrectionMs(correction.correctedUtcMs - Date.now());
    setTimeCorrectionOpen(false);
    showWorkspaceToast('Display time corrected');
    return true;
  };

  const handleResetTimeCorrection = async (): Promise<boolean> => {
    setClockCorrectionMs(0);
    setTimeCorrectionOpen(false);
    showWorkspaceToast('Display time reset');
    return true;
  };

  const profit = metricNumber(accountProfile?.profit);
  const leverage = metricNumber(accountProfile?.leverage);

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
            {accountMode === 'unknown'
              ? 'MODE UNKNOWN'
              : `${accountMode.toUpperCase()} : ${sessionName}`}
          </span>
          {!tradingModeCompatible && (
            <span className="trading-mode-block" role="alert">
              Trading disabled: selected {accountMode.toUpperCase()}, platform {platformAccountMode.toUpperCase()}
            </span>
          )}

          <div className="metric-item">
            <span className="metric-label">BALANCE</span>
            <span className="metric-value neutral">{formatMoney(accountProfile?.balance, accountProfile?.currency)}</span>
          </div>

          <div className="metric-item">
            <span className="metric-label">PROFIT</span>
            <span className={`metric-value ${profit !== null && profit > 0 ? 'positive' : profit !== null && profit < 0 ? 'negative' : 'neutral'}`}>
              {profitDisplay === 'money'
                ? formatMoney(accountProfile?.profit, accountProfile?.currency)
                : formatProfitPercent(accountProfile?.profit, accountProfile?.balance)}
            </span>
          </div>

          <div className="metric-item">
            <span className="metric-label">MARGIN</span>
            <span className="metric-value neutral">{formatMoney(accountProfile?.margin, accountProfile?.currency)}</span>
          </div>

          <div className="metric-item">
            <span className="metric-label">FREE MARGIN</span>
            <span className="metric-value neutral">{formatMoney(accountProfile?.free_margin, accountProfile?.currency)}</span>
          </div>

          <div className="metric-item">
            <span className="metric-label">MARGIN LEVEL</span>
            <span className="metric-value neutral">
              {metricNumber(accountProfile?.margin_level) === null ? '—' : `${metricNumber(accountProfile?.margin_level)?.toFixed(2)}%`}
            </span>
          </div>

          <div className="metric-item">
            <span className="metric-label">LEVERAGE</span>
            <span className="metric-value neutral">{leverage === null ? '—' : `1:${leverage}`}</span>
          </div>

          <div className="metric-item">
            <span className="metric-label">EQUITY</span>
            <span className="metric-value neutral">{formatMoney(accountProfile?.equity, accountProfile?.currency)}</span>
          </div>

          <div className="account-metrics-menu-anchor">
            <button
              type="button"
              className="cme-metric-caret"
              title="Account metric settings"
              aria-label="Account metric settings"
              aria-haspopup="menu"
              aria-expanded={metricsMenuOpen}
              onClick={() => setMetricsMenuOpen((open) => !open)}
            >
              <ChevronLeft size={14} />
            </button>
            <AccountMetricsMenu
              open={metricsMenuOpen}
              accountMode={accountMode}
              leverage={leverage}
              profitDisplay={profitDisplay}
              onProfitDisplayChange={setProfitDisplay}
              onClose={() => setMetricsMenuOpen(false)}
            />
          </div>
        </div>

        {/* Right Info, Confirmation-Mode Toggle & Profile Badge */}
        <div className="cme-header-actions">
          <button
            type="button"
            className={`digital-time${timeMismatch ? ' mismatch' : ''}`}
            aria-label={clock ? `${clock.hour}:${clock.minute}:${clock.second} ${clock.meridiem} ${clock.label} ${clock.date}` : 'clock'}
            aria-haspopup="dialog"
            aria-expanded={timeCorrectionOpen}
            onClick={() => setTimeCorrectionOpen(true)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                setTimeCorrectionOpen(true);
              }
            }}
            title="Correct display time and time zone"
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
          </button>

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
      {timeCorrectionOpen && clock && (
        <TimeCorrectionDialog
          currentUtcMs={Date.now() + clockCorrectionMs}
          timezone={tzValue && parseUtcOffset(tzValue) !== null ? tzValue : 'UTC'}
          onApply={handleApplyTimeCorrection}
          onClose={() => setTimeCorrectionOpen(false)}
          onReset={handleResetTimeCorrection}
        />
      )}

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
