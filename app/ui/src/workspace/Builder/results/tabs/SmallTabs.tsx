import { useState } from 'react';
import { ResultsToolbar, SegmentedButtons } from '../ResultsChrome';
import { SqdCheckbox } from '../../settings/SettingsControls';
import type { Direction, SampleType } from '../resultsFixtures';

/** SP overview tab: stats + traded stocks tree-map header (no shared toolbar). */
export function SpOverviewTab() {
  const [showAll, setShowAll] = useState(false);
  return (
    <div className="sqr-tab">
      <div className="sqr-content sqr-sp-content">
        <div className="sqr-sp-stats" />
        <div className="sqr-sp-treemap-title">
          <div className="title">
            TRADED STOCKS OVERVIEW ({showAll ? 'ALL' : 'TOP 100 BY VOLUME'})
          </div>
          <SqdCheckbox checked={showAll} onChange={setShowAll}>Show all</SqdCheckbox>
        </div>
        <div className="sqr-sp-treemap" />
      </div>
    </div>
  );
}

/** Trade analysis tab: shared toolbar + Period by segmented + empty panels area. */
export function TradeAnalysisTab() {
  const [direction, setDirection] = useState<Direction>('both');
  const [sampleType, setSampleType] = useState<SampleType>('full');
  const [period, setPeriod] = useState(1);
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
          <label>Period by</label>
          <SegmentedButtons
            ariaLabel="Period by"
            options={[
              { value: 1, label: 'Open Time' },
              { value: 2, label: 'Close Time' },
            ]}
            value={period}
            onChange={setPeriod}
          />
        </ResultsToolbar>
      </div>
      <div className="sqr-content sqr-ta-content" />
    </div>
  );
}

/** Profile chart tab: empty until a result provides chart paths (no toolbar). */
export function ProfileChartTab() {
  return (
    <div className="sqr-tab">
      <div className="sqr-content sqr-profile-content" />
    </div>
  );
}

/** Strategy config tab: empty-state label. */
export function StrategyConfigTab() {
  return (
    <div className="sqr-tab">
      <div className="sqr-content sqr-config-content">
        <label className="sqr-info-label">No strategy selected.</label>
      </div>
    </div>
  );
}

/** Custom analysis tab (user ResultsPlugins; demo fixture panel). */
export function CustomAnalysisTab({ name }: { name: string }) {
  return (
    <div className="sqr-tab sqr-custom-tab">
      <div className="sqr-content sqr-custom-content">
        <div className="sqr-custom-box">
          <h3>{name}</h3>
          <p>
            This is a custom analysis plugin tab. It is a standalone
            HTML/Javascript application that can load and present backtest
            results of the selected strategy.
          </p>
          <p>Select a strategy in the databank to load its results here.</p>
        </div>
      </div>
    </div>
  );
}
