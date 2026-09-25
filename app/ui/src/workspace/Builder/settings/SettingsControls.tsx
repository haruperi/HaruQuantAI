import { Settings } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';

/**
 * Donor-look shared controls for the Full settings tabs (donor evidence
 * SQX144-EV-000038..043): sq-fieldset with legend, sq-wradio radios with
 * mark, sqn-spinner with -/+ buttons, sq-slider, plain checkboxes, select
 * boxes, and the additional-config gear popup shell. All styled by the
 * sqd-settings-* classes in the theme-aware skin.
 */

export function SqdFieldset({ legend, children, className }: { legend?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <fieldset className={`sqd-fieldset${className ? ` ${className}` : ''}`}>
      {legend !== undefined && <legend>{legend}</legend>}
      {children}
    </fieldset>
  );
}

export function SqdRadio({
  name,
  value,
  checked,
  onChange,
  disabled,
  children,
}: {
  name: string;
  value: string;
  checked: boolean;
  onChange: (value: string) => void;
  disabled?: boolean;
  children: ReactNode;
}) {
  return (
    <label className={`sqd-wradio${disabled ? ' disabled' : ''}`}>
      <input
        type="radio"
        name={name}
        value={value}
        checked={checked}
        disabled={disabled}
        onChange={() => onChange(value)}
      />
      <span className="sqd-mark" />
      <span className="sqd-wradio-text">{children}</span>
    </label>
  );
}

export function SqdSpinner({
  value,
  onChange,
  min = 0,
  max = 1000000,
  step = 1,
  disabled,
  ariaLabel,
}: {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  disabled?: boolean;
  ariaLabel: string;
}) {
  const clamp = (v: number) => Math.min(max, Math.max(min, v));
  return (
    <span className="sqd-spinner">
      <input
        type="text"
        className="sqd-input"
        style={{ width: `${Math.max(3, String(value).length) + 1}ch` }}
        value={value}
        disabled={disabled}
        aria-label={ariaLabel}
        onChange={e => {
          const parsed = Number(e.target.value.replace(/[^0-9.-]/g, ''));
          if (!Number.isNaN(parsed)) onChange(clamp(parsed));
        }}
      />
      <span className="sqd-spinner-btns">
        <button type="button" className="sqd-spinner-minus" disabled={disabled} aria-label={`Decrease ${ariaLabel}`} onClick={() => onChange(clamp(value - step))} />
        <button type="button" className="sqd-spinner-plus" disabled={disabled} aria-label={`Increase ${ariaLabel}`} onClick={() => onChange(clamp(value + step))} />
      </span>
    </span>
  );
}

export function SqdSlider({
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  postfix = '',
  ariaLabel,
}: {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  postfix?: string;
  ariaLabel: string;
}) {
  return (
    <span className="sqd-slider">
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        aria-label={ariaLabel}
        onChange={e => onChange(Number(e.target.value))}
      />
      <output>{value}{postfix}</output>
    </span>
  );
}

export function SqdCheckbox({
  checked,
  onChange,
  disabled,
  children,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  children: ReactNode;
}) {
  return (
    <label className={`sqd-check${disabled ? ' disabled' : ''}`}>
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={e => onChange(e.target.checked)}
      />
      <span className="sqd-check-mark" />
      <span className="sqd-check-text">{children}</span>
    </label>
  );
}

export function SqdSelect({
  value,
  onChange,
  options,
  disabled,
  ariaLabel,
  width,
}: {
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  disabled?: boolean;
  ariaLabel: string;
  width?: number;
}) {
  const current = options.find(o => o.value === value) ?? options[0];
  return (
    <span className="sqd-select" style={width ? { width } : undefined}>
      <span>{current?.label ?? value}</span>
      <select aria-label={ariaLabel} value={value} disabled={disabled} onChange={e => onChange(e.target.value)}>
        {options.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </span>
  );
}

export function SqdTextInput({
  value,
  onChange,
  ariaLabel,
  width,
}: {
  value: string;
  onChange: (value: string) => void;
  ariaLabel: string;
  width?: number;
}) {
  return (
    <input
      type="text"
      className="sqd-input sqd-text"
      style={width ? { width } : undefined}
      aria-label={ariaLabel}
      value={value}
      onChange={e => onChange(e.target.value)}
    />
  );
}

/** Help link that opens the donor documentation page in a new tab. */
export function SqdHelpLink({ url }: { url: string }) {
  return (
    <a
      className="sqd-link-button"
      href={url}
      target="_blank"
      rel="noreferrer noopener"
    >
      What is it?
    </a>
  );
}

/** Gear-link row opener for the "Additional build config" popups. */
export function GearLink({ onClick, title }: { onClick: () => void; title: string }) {
  return (
    <button type="button" className="sqd-gear-link" title={title} aria-label={`Configure ${title}`} onClick={onClick}>
      <Settings size={13} aria-hidden="true" />
    </button>
  );
}

/** The additional-config popup shell: "{Setting} settings" with Help / Reset / Close / Save. */
export function AdditionalConfigPopup({
  setting,
  onHelp,
  onClose,
  onSave,
  onReset,
  children,
}: {
  setting: string;
  onHelp: () => void;
  onClose: () => void;
  onSave: () => void;
  onReset?: () => void;
  children: ReactNode;
}) {
  useEffect(() => {
    const close = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', close);
    return () => document.removeEventListener('keydown', close);
  }, [onClose]);
  return (
    <div className="modal-backdrop sqx-dialog-scope sqd-dialog-scope" role="presentation" onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <div className="modal sqx-modal sqd-modal" role="dialog" aria-modal="true" style={{ width: 560 }}>
        <header>
          <h2>{setting} settings</h2>
          <button type="button" className="sqx-modal-close" aria-label="Close" onClick={onClose}>&times;</button>
        </header>
        <div className="modal-content sqd-acp-body">{children}</div>
        <footer>
          <button type="button" className="sqd-btn" onClick={onHelp}>Help</button>
          <button type="button" className="sqd-modal-close-link" onClick={onReset} disabled={!onReset}>Reset to default</button>
          <button type="button" className="sqd-modal-close-link" onClick={onClose}>Close</button>
          <button type="button" className="sqd-btn sqd-btn-primary" onClick={onSave}>Save</button>
        </footer>
      </div>
    </div>
  );
}

/** Small hook for open/close popups keyed by string id. */
export function useOpenState(): [string | null, (id: string | null) => void, () => void] {
  const [open, setOpen] = useState<string | null>(null);
  return [open, setOpen, () => setOpen(null)];
}
