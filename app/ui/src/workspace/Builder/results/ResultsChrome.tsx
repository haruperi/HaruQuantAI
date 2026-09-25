import { useEffect, useRef, useState, type ReactNode } from 'react';
import { ChevronDown } from 'lucide-react';
import {
  directionOptions,
  sampleListIn,
  sampleListOut,
  type Direction,
  type SampleType,
} from './resultsFixtures';

/**
 * Shared chrome for the Results tab parity (FEAT-UI-BUILDER_RESULTS_TAB).
 * Mirrors the donor's resultsToolbar directive and quant-tabs strip pieces.
 */

/** Lightweight dropdown with outside-click and Escape close (donor dropdown-menu). */
export function SqrDropdown({
  open,
  onClose,
  children,
  className,
}: {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div ref={ref} className={`sqr-dropdown-menu${className ? ` ${className}` : ''}`}>
      {children}
    </div>
  );
}

/** Segmented button group (donor btn-group: idle #464646, active #36648B). */
export function SegmentedButtons<T extends string | number>({
  options,
  value,
  onChange,
  ariaLabel,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
  ariaLabel: string;
}) {
  return (
    <div className="sqr-seg" role="group" aria-label={ariaLabel}>
      {options.map(o => (
        <button
          key={String(o.value)}
          type="button"
          className={o.value === value ? 'active' : ''}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

/** Sample split button (IS/OOS): label button + caret dropdown (extended mode). */
function SampleSplitButton({
  label,
  active,
  items,
  onSelect,
}: {
  label: string;
  active: boolean;
  items: string[];
  onSelect: () => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="sqr-seg sqr-seg-split">
      <button type="button" className={active ? 'active' : ''} onClick={onSelect}>
        <span className="sqr-sample-name">{label}</span>
      </button>
      <button
        type="button"
        aria-label={`${label} options`}
        className={`sqr-caret${active ? ' active' : ''}`}
        onClick={() => setOpen(v => !v)}
      >
        <ChevronDown size={10} strokeWidth={2.5} />
      </button>
      <SqrDropdown open={open} onClose={() => setOpen(false)}>
        {items.map(item => (
          <a
            key={item}
            role="button"
            tabIndex={0}
            onClick={() => {
              setOpen(false);
              onSelect();
            }}
            onKeyDown={e => {
              if (e.key === 'Enter') {
                setOpen(false);
                onSelect();
              }
            }}
          >
            {item}
          </a>
        ))}
      </SqrDropdown>
    </div>
  );
}

/**
 * Shared results toolbar: Data select + Direction segmented + Sample group +
 * per-tab extras. `extendedSample` switches the sample group to split buttons
 * with caret menus (donor ext-sample-type attribute).
 */
export function ResultsToolbar({
  dataKey,
  direction,
  sampleType,
  onDirectionChange,
  onSampleTypeChange,
  extendedSample,
  showDataSelect = true,
  showDirection = true,
  showSample = true,
  children,
}: {
  dataKey?: string;
  direction: Direction;
  sampleType: SampleType;
  onDirectionChange: (d: Direction) => void;
  onSampleTypeChange: (s: SampleType) => void;
  extendedSample?: boolean;
  showDataSelect?: boolean;
  showDirection?: boolean;
  showSample?: boolean;
  children?: ReactNode;
}) {
  return (
    <div className="sqr-toolbar">
      {showDataSelect && (
        <>
          <label>Data</label>
          <span className="sqd-select sqr-data-select">
            <span>{dataKey ?? ''}</span>
          </span>
        </>
      )}
      {showDirection && (
        <>
          <label>Direction</label>
          <SegmentedButtons
            ariaLabel="Direction"
            options={directionOptions}
            value={direction}
            onChange={onDirectionChange}
          />
        </>
      )}
      {showSample && (
        <>
          <label>Sample</label>
          {extendedSample ? (
            <div className="sqr-sample-group">
              <div className="sqr-seg">
                <button
                  type="button"
                  className={sampleType === 'full' ? 'active' : ''}
                  onClick={() => onSampleTypeChange('full')}
                >
                  Full
                </button>
              </div>
              <SampleSplitButton
                label="IS"
                active={sampleType === 'in'}
                items={sampleListIn}
                onSelect={() => onSampleTypeChange('in')}
              />
              <SampleSplitButton
                label="OOS"
                active={sampleType === 'out'}
                items={sampleListOut}
                onSelect={() => onSampleTypeChange('out')}
              />
            </div>
          ) : (
            <SegmentedButtons
              ariaLabel="Sample"
              options={[
                { value: 'full' as SampleType, label: 'Full' },
                { value: 'in' as SampleType, label: 'IS' },
                { value: 'out' as SampleType, label: 'OOS' },
              ]}
              value={sampleType}
              onChange={onSampleTypeChange}
            />
          )}
        </>
      )}
      {children}
    </div>
  );
}
