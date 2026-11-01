import { useState } from 'react';
import {
  AlarmClock, AlignLeft, Bell, CalendarDays, ChartCandlestick, ChartNoAxesCombined,
  ChevronDown, Paintbrush, Scaling, X,
} from 'lucide-react';
import { useStore } from 'zustand';
import { useChart } from '../../hooks/useChartEngine';
import { defaults } from '../../store/chartStore';
import { chartStyles, type Settings } from '../../types';
import { zones } from '../bottombar/BottomBar';
import { Modal } from '../Modal';

const sections = [
  { id: 'symbol', label: 'Symbol', icon: ChartCandlestick },
  { id: 'status', label: 'Status line', icon: AlignLeft },
  { id: 'scales', label: 'Scales and lines', icon: Scaling },
  { id: 'canvas', label: 'Canvas', icon: Paintbrush },
  { id: 'trading', label: 'Trading', icon: ChartNoAxesCombined },
  { id: 'alerts', label: 'Alerts', icon: Bell },
  { id: 'events', label: 'Events', icon: CalendarDays },
] as const;
type Section = (typeof sections)[number]['id'];

const templateKey = 'haruquantai.chart.settings.templates.v1';
type Templates = Record<string, Partial<Settings>>;
const isRecord = (v: unknown): v is Record<string, unknown> =>
  typeof v === 'object' && v !== null && !Array.isArray(v);

function loadTemplates(): Templates {
  if (typeof window === 'undefined') return {};
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(templateKey) || '{}');
    if (!isRecord(parsed)) return {};
    const templates: Templates = {};
    for (const [name, source] of Object.entries(parsed).slice(0, 20)) {
      if (!isRecord(source) || name.length > 64) continue;
      const values: Record<string, unknown> = {};
      for (const [key, base] of Object.entries(defaults)) {
        const value = source[key];
        if (typeof value === typeof base &&
            (typeof value !== 'string' || value.length <= 100))
          values[key] = value;
      }
      templates[name] = values as Partial<Settings>;
    }
    return templates;
  } catch {
    return {};
  }
}

function palette(theme: Settings['theme']): Partial<Settings> {
  return theme === 'light'
    ? { theme, backgroundColor: '#ffffff', gridColor: '#e6e8ed', textColor: '#787b86' }
    : { theme, backgroundColor: '#131722', gridColor: '#2a2e39', textColor: '#787b86' };
}

function Checkbox({
  label, checked, onChange, disabled = false, hint,
}: {
  label: string;
  checked: boolean;
  onChange: (next: boolean) => void;
  disabled?: boolean;
  hint?: string;
}) {
  return (
    <label className={'cq-setting-check' + (disabled ? ' cq-setting-disabled' : '')}>
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} disabled={disabled} />
      <span>{label}{hint && <small>{hint}</small>}</span>
    </label>
  );
}

function ColorPair({
  label, enabled, onEnabled, up, down, onUp, onDown,
}: {
  label: string;
  enabled: boolean;
  onEnabled: (value: boolean) => void;
  up: string;
  down: string;
  onUp: (value: string) => void;
  onDown: (value: string) => void;
}) {
  return (
    <div className="cq-setting-color-row">
      <Checkbox label={label} checked={enabled} onChange={onEnabled} />
      <div className="cq-setting-colors">
        <input type="color" aria-label={label + ' up color'} value={up} onChange={(e) => onUp(e.target.value)} disabled={!enabled} />
        <input type="color" aria-label={label + ' down color'} value={down} onChange={(e) => onDown(e.target.value)} disabled={!enabled} />
      </div>
    </div>
  );
}

export function SettingsDialog() {
  const { store } = useChart();
  const chart = useStore(store, (state) => state.chart);
  const [draft, setDraft] = useState<Settings>(() => ({ ...chart }));
  const [section, setSection] = useState<Section>('symbol');
  const [customPrecision, setCustomPrecision] = useState(chart.precision !== defaults.precision);
  const [customTimezone, setCustomTimezone] = useState(chart.timezone !== defaults.timezone);
  const [templates, setTemplates] = useState<Templates>(loadTemplates);
  const [templateError, setTemplateError] = useState('');
  const change = (patch: Partial<Settings>) => setDraft((previous) => ({ ...previous, ...patch }));
  const toggle = (key: keyof Settings) => (checked: boolean) =>
    change({ [key]: checked } as Partial<Settings>);
  const close = () => store.getState().setUI({ dialog: null });
  const apply = () => {
    store.getState().settings(draft);
    close();
  };
  const applyTemplate = (values: Partial<Settings>) => {
    // Templates are visual preferences, never a request to switch the security or timeframe.
    const { symbol: _symbol, interval: _interval, range: _range, title: _title, ...rest } = values;
    void _symbol; void _interval; void _range; void _title;
    change(rest);
    if (rest.precision !== undefined) setCustomPrecision(rest.precision !== defaults.precision);
    if (rest.timezone !== undefined) setCustomTimezone(rest.timezone !== defaults.timezone);
  };
  const saveTemplate = () => {
    const name = window.prompt('Save chart settings template as:', 'My chart template')?.trim();
    if (!name) return;
    if (name.length > 64) { setTemplateError('Template name must be 64 characters or less.'); return; }
    const next = { ...templates, [name]: draft };
    try {
      localStorage.setItem(templateKey, JSON.stringify(next));
      setTemplates(next);
      setTemplateError('');
    } catch {
      setTemplateError('Unable to save template in browser storage.');
    }
  };

  const footer = (
    <footer className="cq-settings-footer">
      <div className="cq-settings-template">
        <details>
          <summary>Template <ChevronDown size={15} aria-hidden="true" /></summary>
          <div className="cq-settings-template-popover">
            <button onClick={() => applyTemplate(defaults)}>Restore defaults</button>
            <button onClick={() => applyTemplate(palette('dark'))}>Dark canvas</button>
            <button onClick={() => applyTemplate(palette('light'))}>Light canvas</button>
            {Object.entries(templates).map(([name, template]) => (
              <div className="cq-settings-template-entry" key={name}>
                <button onClick={() => applyTemplate(template)}>{name}</button>
                <button aria-label={'Delete template ' + name} title="Delete template" onClick={() => {
                  const next = { ...templates };
                  delete next[name];
                  try {
                    localStorage.setItem(templateKey, JSON.stringify(next));
                    setTemplates(next);
                    setTemplateError('');
                  } catch {
                    setTemplateError('Unable to delete template from browser storage.');
                  }
                }}><X size={13} /></button>
              </div>
            ))}
            <div className="cq-settings-template-divider" />
            <button onClick={saveTemplate}>Save as template…</button>
          </div>
        </details>
        {templateError && <small role="alert">{templateError}</small>}
      </div>
      <div className="cq-settings-footer-buttons">
        <button onClick={close}>Cancel</button>
        <button className="cq-settings-ok" onClick={apply}>Ok</button>
      </div>
    </footer>
  );

  return (
    <Modal title="Chart settings" className="cq-settings-modal" footer={footer}>
      <div className="cq-settings-layout">
        <nav aria-label="Chart settings sections" className="cq-settings-sidebar">
          {sections.map(({ id, label, icon: Icon }) => (
            <button key={id} type="button" className={section === id ? 'cq-settings-selected' : ''}
              aria-current={section === id ? 'page' : undefined}
              onClick={() => setSection(id)}>
              <Icon aria-hidden="true" size={19} strokeWidth={1.7} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="cq-settings-main" role="region" aria-label={sections.find((s) => s.id === section)?.label + ' settings'}>
          {section === 'symbol' && (
            <>
              <div className="cq-setting-heading">CHART TYPE</div>
              <label className="cq-setting-field">
                Style
                <select value={draft.style} onChange={(e) => change({ style: e.target.value as Settings['style'] })}>
                  {chartStyles.map((style) => <option key={style} value={style}>{style}</option>)}
                </select>
              </label>
              <div className="cq-setting-heading">CANDLES</div>
              <Checkbox label="Color bars based on previous close" checked={draft.colorBarsByPreviousClose} onChange={toggle('colorBarsByPreviousClose')} />
              <ColorPair label="Body" enabled={draft.candleBody} onEnabled={toggle('candleBody')}
                up={draft.candleUpColor} down={draft.candleDownColor}
                onUp={(color) => change({ candleUpColor: color })}
                onDown={(color) => change({ candleDownColor: color })} />
              <ColorPair label="Borders" enabled={draft.candleBorders} onEnabled={toggle('candleBorders')}
                up={draft.candleBorderUpColor} down={draft.candleBorderDownColor}
                onUp={(color) => change({ candleBorderUpColor: color })}
                onDown={(color) => change({ candleBorderDownColor: color })} />
              <ColorPair label="Wick" enabled={draft.candleWicks} onEnabled={toggle('candleWicks')}
                up={draft.candleWickUpColor} down={draft.candleWickDownColor}
                onUp={(color) => change({ candleWickUpColor: color })}
                onDown={(color) => change({ candleWickDownColor: color })} />
              <div className="cq-setting-heading">DATA MODIFICATION</div>
              <Checkbox label="Adjust data for dividends" checked={false} onChange={() => {}} disabled
                hint="Not available for the current simulated market-data source." />
              <div className="cq-setting-inline">
                <Checkbox label="Precision" checked={customPrecision} onChange={(checked) => {
                  setCustomPrecision(checked);
                  if (!checked) change({ precision: defaults.precision });
                }} />
                <select aria-label="Price precision" disabled={!customPrecision} value={draft.precision}
                  onChange={(e) => change({ precision: Number(e.target.value) })}>
                  {Array.from({ length: 9 }, (_, i) => <option key={i} value={i}>{i === defaults.precision ? 'Default (' + i + ')' : i + ' decimals'}</option>)}
                </select>
              </div>
              <div className="cq-setting-inline">
                <Checkbox label="Timezone" checked={customTimezone} onChange={(checked) => {
                  setCustomTimezone(checked);
                  if (!checked) change({ timezone: defaults.timezone });
                }} />
                <select aria-label="Chart timezone" disabled={!customTimezone} value={draft.timezone}
                  onChange={(e) => change({ timezone: e.target.value })}>
                  {zones.map((zone) => <option key={zone} value={zone}>{zone}</option>)}
                </select>
              </div>
              <Checkbox label="Display inactivity gaps on intraday" checked={!draft.gaps}
                onChange={(checked) => change({ gaps: !checked })}
                hint="Uses actual timestamp spacing; includes non-trading session gaps with the current feed." />
            </>
          )}
          {section === 'status' && (
            <>
              <div className="cq-setting-heading">STATUS LINE</div>
              <Checkbox label="Symbol name and exchange" checked={draft.showSymbolTitle} onChange={toggle('showSymbolTitle')} />
              <Checkbox label="OHLC values and change" checked={draft.showOhlc} onChange={toggle('showOhlc')} />
              <Checkbox label="Indicator titles and values" checked={draft.showIndicatorLegend} onChange={toggle('showIndicatorLegend')} />
              <Checkbox label="Floating OHLC values on hover" checked={draft.tooltip} onChange={toggle('tooltip')} />
              <Checkbox label="Countdown to bar close" checked={draft.countdown} onChange={toggle('countdown')} />
            </>
          )}
          {section === 'scales' && (
            <>
              <div className="cq-setting-heading">PRICE SCALE</div>
              <label className="cq-setting-field">Scale mode
                <select value={draft.scale} onChange={(e) => change({ scale: e.target.value as Settings['scale'] })}>
                  <option value="linear">Regular</option>
                  <option value="log">Logarithmic</option>
                  <option value="percent">Percentage</option>
                  <option value="indexed">Indexed to 100</option>
                </select>
              </label>
              <Checkbox label="Auto scale" checked={draft.auto} onChange={toggle('auto')} />
              <Checkbox label="Invert scale" checked={draft.reverse} onChange={toggle('reverse')} />
              <Checkbox label="Price scale labels" checked={draft.showPriceScaleLabels} onChange={toggle('showPriceScaleLabels')} />
              <div className="cq-setting-heading">LINES</div>
              <Checkbox label="Last price line" checked={draft.showLastPriceLine} onChange={toggle('showLastPriceLine')} />
              <Checkbox label="Previous day close" checked={draft.previousClose} onChange={toggle('previousClose')} />
            </>
          )}
          {section === 'canvas' && (
            <>
              <div className="cq-setting-heading">APPEARANCE</div>
              <label className="cq-setting-field">Theme
                <select aria-label="Chart theme" value={draft.theme}
                  onChange={(e) => change(palette(e.target.value as Settings['theme']))}>
                  <option value="dark">Dark</option><option value="light">Light</option>
                </select>
              </label>
              <label className="cq-setting-color-field">Background
                <input type="color" aria-label="Chart background color" value={draft.backgroundColor} onChange={(e) => change({ backgroundColor: e.target.value })} />
              </label>
              <Checkbox label="Grid lines" checked={draft.showGrid} onChange={toggle('showGrid')} />
              <label className="cq-setting-color-field">Grid lines color
                <input type="color" aria-label="Chart grid color" value={draft.gridColor} onChange={(e) => change({ gridColor: e.target.value })} disabled={!draft.showGrid} />
              </label>
              <label className="cq-setting-color-field">Scale and axis text color
                <input type="color" aria-label="Chart axis text color" value={draft.textColor} onChange={(e) => change({ textColor: e.target.value })} />
              </label>
              <Checkbox label="Volume histogram" checked={draft.volume} onChange={toggle('volume')} />
              <Checkbox label="History minimap" checked={draft.minimap} onChange={toggle('minimap')} />
            </>
          )}
          {section === 'trading' && (
            <>
              <div className="cq-setting-heading">ON-CHART TRADING</div>
              <Checkbox label="Buy and Sell buttons" checked={draft.showBuySellButtons} onChange={toggle('showBuySellButtons')} />
              <Checkbox label="Display open and pending positions" checked={draft.showPositions} onChange={toggle('showPositions')} />
              <p className="cq-settings-note">Current chart orders and positions use the simulated trading engine. These controls only change visibility, not execution or risk settings.</p>
            </>
          )}
          {section === 'alerts' && (
            <>
              <div className="cq-setting-heading">ALERT VISIBILITY</div>
              <Checkbox label="Show active alert lines" checked={draft.showAlertLines} onChange={toggle('showAlertLines')} />
              <p className="cq-settings-note">Hiding alert lines does not disable alert evaluation or notifications. Manage alert conditions from the Alerts panel.</p>
            </>
          )}
          {section === 'events' && (
            <>
              <div className="cq-setting-heading">CHART EVENTS</div>
              <Checkbox label="Session breaks" checked={draft.sessions} onChange={toggle('sessions')} />
              <Checkbox label="Show inactivity gaps" checked={!draft.gaps} onChange={(checked) => change({ gaps: !checked })} />
              <div className="cq-setting-heading">CORPORATE EVENTS</div>
              <Checkbox label="Earnings" checked={false} onChange={() => {}} disabled />
              <Checkbox label="Dividends" checked={false} onChange={() => {}} disabled />
              <Checkbox label="Splits" checked={false} onChange={() => {}} disabled />
              <p className="cq-settings-note">Corporate events require an authenticated market-events feed and are not provided by the current simulated feed.</p>
            </>
          )}
        </div>
      </div>
    </Modal>
  );
}
