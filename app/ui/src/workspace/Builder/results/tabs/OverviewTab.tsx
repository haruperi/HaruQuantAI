import { useState } from 'react';
import { ResultsToolbar } from '../ResultsChrome';
import { overviewTemplates, type Direction, type SampleType } from '../resultsFixtures';

/** Overview results tab: toolbar + Template select + empty overview area. */
export function OverviewTab() {
  const [direction, setDirection] = useState<Direction>('both');
  const [sampleType, setSampleType] = useState<SampleType>('full');
  const [template, setTemplate] = useState('SQDefault');
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
          <label>Template</label>
          <span className="sqd-select">
            <span>
              {overviewTemplates.find(t => t.value === template)?.label ?? template}
            </span>
            <select
              aria-label="Template"
              value={template}
              onChange={e => setTemplate(e.target.value)}
            >
              {overviewTemplates.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </span>
        </ResultsToolbar>
      </div>
      <div className="sqr-content sqr-overview-content">
        <h3 className="sqr-no-strategy">No strategy selected</h3>
      </div>
    </div>
  );
}
