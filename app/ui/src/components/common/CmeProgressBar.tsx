'use client';

import React from 'react';

export interface CmeProgressBarProps {
  /** Current progress value (0 to max). */
  value: number;
  /** Maximum value representing 100% completion (default: 100). */
  max?: number;
  /** Primary label displayed above or next to the bar. */
  label?: string;
  /** Secondary detailed status message (e.g. "Page 2 of 4"). */
  subtext?: string;
  /** Color theme variant (default: 'blue'). */
  variant?: 'blue' | 'green' | 'amber';
  /** Custom height in pixels (default: 8). */
  height?: number;
  /** Whether the total duration is unknown (renders animated shimmer). */
  indeterminate?: boolean;
}

export const CmeProgressBar: React.FC<CmeProgressBarProps> = ({
  value,
  max = 100,
  label,
  subtext,
  variant = 'blue',
  height = 8,
  indeterminate = false,
}) => {
  const percentage = indeterminate
    ? 100
    : Math.min(100, Math.max(0, Math.round((value / (max || 1)) * 100)));

  const fillColor =
    variant === 'green'
      ? 'var(--financial-positive, #00e473)'
      : variant === 'amber'
        ? 'var(--accent-amber, #ffb300)'
        : 'var(--cme-blue-bright, #3cc8ff)';

  return (
    <div
      className="cme-progress-container"
      role="progressbar"
      aria-valuenow={indeterminate ? undefined : percentage}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label ?? 'Loading progress'}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
        width: '100%',
        padding: '12px 16px',
        backgroundColor: 'rgba(8, 29, 55, 0.65)',
        border: '1px solid var(--cme-navy-border, #1e3a5f)',
        borderRadius: '6px',
        boxSizing: 'border-box',
      }}
    >
      {(label || subtext || !indeterminate) && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '11px',
            fontWeight: 600,
            color: 'var(--text-light-grey, #dbdbdb)',
          }}
        >
          <span>{label ?? 'Processing…'}</span>
          <span>
            {subtext ? `${subtext} (${percentage}%)` : `${percentage}%`}
          </span>
        </div>
      )}

      {/* Progress Track */}
      <div
        style={{
          width: '100%',
          height: `${height}px`,
          backgroundColor: 'rgba(255, 255, 255, 0.08)',
          borderRadius: `${Math.round(height / 2)}px`,
          overflow: 'hidden',
          position: 'relative',
          boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.3)',
        }}
      >
        {/* Progress Fill */}
        <div
          style={{
            width: `${percentage}%`,
            height: '100%',
            backgroundColor: fillColor,
            borderRadius: `${Math.round(height / 2)}px`,
            transition: 'width 0.25s ease-out',
            boxShadow: `0 0 10px ${fillColor}80`,
            animation: indeterminate ? 'cmeShimmer 1.5s infinite linear' : undefined,
          }}
        />
      </div>
    </div>
  );
};
