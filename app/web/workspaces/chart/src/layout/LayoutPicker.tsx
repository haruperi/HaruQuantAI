import { useEffect, useRef, useState } from 'react';
import { ChevronDown, PanelsTopLeft } from 'lucide-react';
import { getLayout, layoutGroups, type LayoutDefinition, type LayoutState, type SyncSetting } from './layouts';

export interface LayoutPickerProps {
  value: LayoutState;
  onLayoutChange: (id: string) => void;
  onSyncChange: (setting: SyncSetting, enabled: boolean) => void;
}
const switches: { key: SyncSetting; title: string; description: string }[] = [
  { key: 'symbol', title: 'Symbol', description: 'Use the same symbol in every chart' },
  { key: 'interval', title: 'Interval', description: 'Use the same resolution in every chart' },
  { key: 'crosshair', title: 'Crosshair', description: 'Show crosshair time across charts' },
  { key: 'time', title: 'Time', description: 'Synchronize visible time windows when panning or zooming' },
  { key: 'dateRange', title: 'Date range', description: 'Synchronize the chart date-range preset' },
];
function Preview({ definition }: { definition: LayoutDefinition }) {
  const { cells, count } = definition;
  return (
    <span className="cq-layout-preview" aria-hidden="true"
      style={{
        gridTemplateColumns: 'repeat(' + cells[0].length + ', minmax(0, 1fr))',
        gridTemplateRows: 'repeat(' + cells.length + ', minmax(0, 1fr))',
        gridTemplateAreas: cells.map(row => '"' + row.map(cell => 'c' + cell).join(' ') + '"').join(' '),
      }}
    >
      {Array.from({ length: count }, (_, i) =>
        <span key={i} style={{ gridArea: 'c' + i }} />)}
    </span>
  );
}
export function LayoutPicker({ value, onLayoutChange, onSyncChange }: LayoutPickerProps) {
  const [open, setOpen] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const outside = (event: PointerEvent) => {
      if (!container.current?.contains(event.target as Node)) setOpen(false);
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('pointerdown', outside);
    document.addEventListener('keydown', escape);
    return () => {
      document.removeEventListener('pointerdown', outside);
      document.removeEventListener('keydown', escape);
    };
  }, [open]);
  return (
    <div className="cq-layout-control" ref={container}>
      <button aria-label="Select layout" aria-haspopup="dialog" aria-expanded={open}
        title={'Select layout · ' + getLayout(value.id).label}
        className={open || value.id !== 's' ? 'cq-active' : ''}
        onClick={() => setOpen(previous => !previous)}>
        <PanelsTopLeft size={19} aria-hidden="true" />
        <ChevronDown size={11} aria-hidden="true" />
      </button>
      {open && (
        <div className="cq-layout-popover" role="dialog" aria-label="Select layout">
          <div className="cq-layout-options">
            {layoutGroups.map(group => (
              <div className="cq-layout-option-group" key={group.count}>
                <span className="cq-layout-group-count">{group.count}</span>
                <div className="cq-layout-option-list">
                  {group.ids.map(id => (
                    <button
                      key={id}
                      aria-label={getLayout(id).label}
                      title={getLayout(id).label}
                      aria-pressed={value.id === id}
                      className={'cq-layout-choice' + (value.id === id ? ' cq-layout-choice-active' : '')}
                      onClick={() => { onLayoutChange(id); setOpen(false); }}
                    >
                      <Preview definition={getLayout(id)} />
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="cq-layout-sync">
            <div className="cq-layout-sync-heading">SYNC IN LAYOUT</div>
            {switches.map(item => (
              <div className="cq-layout-sync-row" key={item.key}>
                <span title={item.description}>{item.title}</span>
                <button role="switch" aria-label={'Sync ' + item.title}
                  aria-checked={value.sync[item.key]}
                  title={item.description}
                  onClick={() => onSyncChange(item.key, !value.sync[item.key])}>
                  <span />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
