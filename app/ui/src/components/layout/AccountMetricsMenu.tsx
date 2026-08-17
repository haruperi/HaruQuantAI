'use client';

import React, { useEffect, useRef } from 'react';

interface AccountMetricsMenuProps {
  open: boolean;
  accountMode: string;
  leverage: number | null;
  profitDisplay: 'money' | 'percent';
  onProfitDisplayChange: (display: 'money' | 'percent') => void;
  onClose: () => void;
}

/** Accessible presentation settings for the Header account metrics. */
export const AccountMetricsMenu: React.FC<AccountMetricsMenuProps> = ({
  open,
  accountMode,
  leverage,
  profitDisplay,
  onProfitDisplayChange,
  onClose,
}) => {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const closeOnEscape = (event: KeyboardEvent): void => {
      if (event.key === 'Escape') onClose();
    };
    const closeOutside = (event: MouseEvent): void => {
      if (!panelRef.current?.contains(event.target as Node)) onClose();
    };
    document.addEventListener('keydown', closeOnEscape);
    document.addEventListener('mousedown', closeOutside);
    return () => {
      document.removeEventListener('keydown', closeOnEscape);
      document.removeEventListener('mousedown', closeOutside);
    };
  }, [open, onClose]);

  if (!open) return null;
  const simWithoutSession = accountMode === 'sim' && leverage === null;

  return (
    <div ref={panelRef} className="account-metrics-menu" role="menu" aria-label="Account metric settings">
      <fieldset>
        <legend>Profit display</legend>
        <label>
          <input
            type="radio"
            name="profit-display"
            value="money"
            checked={profitDisplay === 'money'}
            onChange={() => onProfitDisplayChange('money')}
          /> Money
        </label>
        <label>
          <input
            type="radio"
            name="profit-display"
            value="percent"
            checked={profitDisplay === 'percent'}
            onChange={() => onProfitDisplayChange('percent')}
          /> Percent
        </label>
      </fieldset>
      <label className="metric-leverage-setting">
        Leverage
        <input
          type="number"
          min="1"
          step="1"
          value={leverage ?? ''}
          disabled
          readOnly
          aria-describedby="leverage-setting-note"
        />
      </label>
      <span id="leverage-setting-note" className="metric-setting-note">
        {simWithoutSession
          ? 'Start a simulation session to configure its leverage.'
          : accountMode === 'sim'
            ? 'Simulation-session leverage is read-only here.'
            : 'Leverage is supplied automatically by MT5.'}
      </span>
    </div>
  );
};
