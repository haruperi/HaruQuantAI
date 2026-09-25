import { useState } from 'react';
import { Cog } from 'lucide-react';
import { ResultsToolbar } from '../ResultsChrome';
import { ExportTradesModal, ManageViewsModal } from '../ResultsModals';
import { SqdCheckbox } from '../../settings/SettingsControls';
import { tradeListViews, type Direction, type SampleType } from '../resultsFixtures';

/** List of trades tab: toolbar extras (View, manage gear, Export, expired) + empty grid. */
export function TradeListTab() {
  const [direction, setDirection] = useState<Direction>('both');
  const [sampleType, setSampleType] = useState<SampleType>('full');
  const [view, setView] = useState('Default');
  const [expired, setExpired] = useState(false);
  const [manageOpen, setManageOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  return (
    <div className="sqr-tab">
      <div className="sqr-toolbar-row">
        <ResultsToolbar
          direction={direction}
          sampleType={sampleType}
          onDirectionChange={setDirection}
          onSampleTypeChange={setSampleType}
          extendedSample
        >
          <span className="sqr-toolbar-right">
            <label>View</label>
            <span className="sqd-select">
              <span>{tradeListViews.find(v => v.value === view)?.label ?? view}</span>
              <select aria-label="View" value={view} onChange={e => setView(e.target.value)}>
                {tradeListViews.map(v => (
                  <option key={v.value} value={v.value}>{v.label}</option>
                ))}
              </select>
            </span>
            <a
              role="button"
              tabIndex={0}
              className="sqr-manage-views-btn"
              aria-label="Manage views"
              title="Manage"
              onClick={() => setManageOpen(true)}
              onKeyDown={e => e.key === 'Enter' && setManageOpen(true)}
            >
              <Cog size={13} />
            </a>
            <button type="button" className="sqd-btn sqr-export-btn" onClick={() => setExportOpen(true)}>
              Export
            </button>
          </span>
          <span className="sqr-include-expired">
            <label>Include expired</label>
            <SqdCheckbox checked={expired} onChange={setExpired}>
              <span className="sqr-visually-hidden">Include expired</span>
            </SqdCheckbox>
          </span>
        </ResultsToolbar>
      </div>
      <div className="sqr-content sqr-grid-content" />
      {manageOpen && <ManageViewsModal onClose={() => setManageOpen(false)} />}
      {exportOpen && <ExportTradesModal onClose={() => setExportOpen(false)} />}
    </div>
  );
}
