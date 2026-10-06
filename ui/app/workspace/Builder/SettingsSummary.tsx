import { useEffect, useRef, useState } from 'react';
import {
  buildOptionRows,
  crossCheckCategories,
  dataSettingsFixture,
  predefinedConfigs,
  toggleCrossCheck,
  displayCrossCheckTitle,
  type CrossCheckTree,
} from './fixtures';

/**
 * SQX-style "Settings summary" column of the Builder Progress tab (donor
 * evidence retained target UI; current donor equivalence unverified): the predefined-config dropdown, the Data
 * rows, the Build options rows (click opens Full settings), and the cross
 * checks switch tree with Disable all. All values are demo fixture truth.
 */

function Switch({ checked, disabled, title }: { checked: boolean; disabled?: boolean; title?: string }) {
  return (
    <span className={`sqd-switch${checked ? ' on' : ''}${disabled ? ' disabled' : ''}`} title={title}>
      <input type="checkbox" checked={checked} readOnly disabled={disabled} aria-hidden="true" tabIndex={-1} />
      <i />
    </span>
  );
}

export function SettingsSummary({ onOpenFullSettings }: { onOpenFullSettings: () => void }) {
  const [configsOpen, setConfigsOpen] = useState(false);
  const [crossChecks, setCrossChecks] = useState<CrossCheckTree>(crossCheckCategories);
  const [disableAll, setDisableAll] = useState(false);
  const configsRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!configsOpen) return;
    const onDocClick = (e: MouseEvent) => {
      if (configsRef.current && !configsRef.current.contains(e.target as Node)) setConfigsOpen(false);
    };
    document.addEventListener('click', onDocClick);
    return () => document.removeEventListener('click', onDocClick);
  }, [configsOpen]);

  const onToggleDisableAll = () => {
    const next = !disableAll;
    setDisableAll(next);
    if (next) {
      setCrossChecks(current => current.map(c => ({ ...c, items: c.items.map(i => ({ ...i, use: false })) })));
    }
  };

  return (
    <div className="sqd-settings-col">
      <div className="sqd-card sqd-simple-settings">
        <div className="sqd-summary-title">Settings summary</div>
        <div className="sqd-predefined" ref={configsRef}>
          <button
            type="button"
            className="sqd-btn"
            aria-haspopup="menu"
            aria-expanded={configsOpen}
            onClick={() => setConfigsOpen(!configsOpen)}
          >
            Use predefined config
            <span className="sqx-caret" />
          </button>
          {configsOpen && (
            <div className="sqx-menu sqd-menu" role="menu">
              {predefinedConfigs.map(config => (
                <button key={config.label} type="button" role="menuitem" title={config.info} onClick={() => setConfigsOpen(false)}>
                  <span>{config.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="sqd-settings-title">Data</div>
        <div className="sqd-setting-row">
          <label className="sqd-label fixed">Engine</label>
          <div className="sqd-select">
            <span>{dataSettingsFixture.engine}</span>
            <select aria-label="Engine" defaultValue={dataSettingsFixture.engine}>
              {dataSettingsFixture.engines.map(engine => (
                <option key={engine}>{engine}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="sqd-setting-row">
          <label className="sqd-label fixed">Symbol</label>
          <div className="sqd-setting-right">
            <div className="sqd-select sqd-data-box">
              <span>{dataSettingsFixture.symbol}</span>
              <select aria-label="Symbol" defaultValue={dataSettingsFixture.symbol}>
                <option>{dataSettingsFixture.symbol}</option>
              </select>
            </div>
            <div className="sqd-select sqd-timeframe">
              <span>{dataSettingsFixture.timeframe}</span>
              <select aria-label="Timeframe" defaultValue={dataSettingsFixture.timeframe}>
                {['M15', 'M30', 'H1', 'H4', 'D1'].map(tf => (
                  <option key={tf}>{tf}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
        <div className="sqd-setting-row sqd-range-row">
          <label className="sqd-label fixed" />
          <label className="sqd-range date">{dataSettingsFixture.dateRange}</label>
          <label className="sqd-range oos">{dataSettingsFixture.oosLabel}</label>
        </div>

        <div className="sqd-settings-title">Build options</div>
        <div className="sqd-build-options" role="list">
          {buildOptionRows.map(row => (
            <button type="button" className="sqd-option-row" key={row.name} onClick={onOpenFullSettings} title="Open Full settings">
              <span>{row.name}</span>
              <span className="sqd-option-value">
                {row.lines.map((line, i) => (
                  <span key={i} className="sqd-option-line">{line}</span>
                ))}
              </span>
            </button>
          ))}
        </div>

        <div className="sqd-settings-title sqd-cross-checks-title">
          Cross checks (strategy robustness tests)
          <span className="sqd-disable-all">
            <button type="button" className="sqd-disable-all-label" onClick={onToggleDisableAll}>
              Disable all
            </button>
            <Switch checked={disableAll} title="Disable all cross checks" />
          </span>
        </div>
        <div className="sqd-cross-checks">
          {crossChecks.map(category => (
            <div className="sqd-cs-section" key={category.name}>
              <div className="sqd-cs-category">
                <span className="sqd-cs-name">{category.name}</span>
              </div>
              {category.items.map(item => (
                <div className="sqd-cs-item" key={item.id}>
                  <button
                    type="button"
                    className="sqd-cs-label"
                    disabled={disableAll}
                    onClick={() => setCrossChecks(current => toggleCrossCheck(current, item.id, disableAll))}
                  >
                    {displayCrossCheckTitle(item.title)}
                  </button>
                  <Switch checked={item.use} disabled={disableAll} title={item.title} />
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
