'use client';

/**
 * Header profile dropdown (FEAT-UI-01, FR-UI-020).
 *
 * Mirrors the CME Group Simulator's profile menu: it drops from the `<`
 * chevron beside the user name and presents the account-mode section plus
 * the real Settings and Logout actions. Every action binds to an existing
 * application mechanism - the trading store's settings modal and the
 * authenticated session's logout route - so the menu never presents a dead
 * or invented control.
 */
import React, { useEffect, useRef } from 'react';
import { ChevronRight, LogOut, Settings } from 'lucide-react';

import {
  SELECTABLE_ACCOUNT_MODES,
  type AccountMode,
  type SelectableAccountMode,
} from '../../features/workspaces';

/** Props for the profile dropdown menu. */
export interface ProfileDropdownProps {
  /** Whether the menu is open. */
  open: boolean;
  /** Close the menu without choosing an action. */
  onClose: () => void;
  /** Open the System Settings modal. */
  onOpenSettings: () => void;
  /** Sign out of the authenticated session. */
  onLogout: () => void;
  /** The account mode currently applied as the app-wide context. */
  accountMode: AccountMode;
  /** Apply a new account mode as the app-wide context. */
  onSelectAccountMode: (mode: SelectableAccountMode) => void;
  /** True while a selection is being persisted; the radios are inert. */
  pending?: boolean;
}

/**
 * Render the profile menu.
 *
 * The menu is absolutely positioned under the profile section; the caller
 * owns open/close state and only renders this component while open. Pressing
 * Escape or clicking outside closes it.
 */
export const ProfileDropdown: React.FC<ProfileDropdownProps> = ({
  open,
  onClose,
  onOpenSettings,
  onLogout,
  accountMode,
  onSelectAccountMode,
  pending = false,
}) => {
  const rootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const handlePointerDown = (event: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        onClose();
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="profile-dropdown" role="menu" aria-label="Profile menu" ref={rootRef}>
      <div className="profile-menu-group">
        <div className="profile-menu-label">Account Mode:</div>
        <div className="profile-menu-row" role="radiogroup" aria-label="Account mode">
          {SELECTABLE_ACCOUNT_MODES.map((mode) => (
            <button
              key={mode}
              type="button"
              // The mode colour is carried by a data attribute rather than the
              // class list so the palette lives in one place in the stylesheet
              // and selected/unselected share it (FR-UI-205).
              className={`profile-mode-option ${accountMode === mode ? 'selected' : ''}`}
              data-mode={mode}
              role="radio"
              aria-checked={accountMode === mode}
              disabled={pending}
              onClick={() => onSelectAccountMode(mode)}
            >
              <span className="profile-radio" aria-hidden="true" />
              <span className="profile-menu-value">{mode.toUpperCase()}</span>
            </button>
          ))}
        </div>
      </div>

      <hr className="profile-menu-divider" />

      <button
        type="button"
        className="profile-menu-item"
        role="menuitem"
        onClick={() => {
          onOpenSettings();
          onClose();
        }}
      >
        <Settings size={14} aria-hidden="true" />
        <span>Settings</span>
        <ChevronRight size={14} className="profile-item-chevron" aria-hidden="true" />
      </button>
      <button
        type="button"
        className="profile-menu-item"
        role="menuitem"
        onClick={() => {
          onLogout();
          onClose();
        }}
      >
        <LogOut size={14} aria-hidden="true" />
        <span>Logout</span>
      </button>
    </div>
  );
};
