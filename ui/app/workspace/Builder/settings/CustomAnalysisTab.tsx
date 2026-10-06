import { SqdFieldset, SqdHelpLink, SqdSelect, SqdTextInput } from './SettingsControls';
import { customAnalysisDefaults, customAnalysisMethodOptions } from './settingsFixtures';

/** "Custom analysis" tab (donor evidence retained target UI; current donor equivalence unverified). */
export function CustomAnalysisTab() {
  const perStrategy = customAnalysisMethodOptions.filter(o => o.group === 'perStrategy');
  const fullDatabank = customAnalysisMethodOptions.filter(o => o.group === 'fullDatabank');

  const row = (label: string, value: string, options: { value: string; label: string }[], args: string, group: string) => (
    <div className="sqd-ca-row" key={`${group}-${label}`}>
      <label className="sqd-label">{label}</label>
      <SqdSelect ariaLabel={`${label} method`} value={value} onChange={() => undefined} options={options} width={260} />
      <label className="sqd-label" style={{ width: 'auto' }}>Input args</label>
      <SqdTextInput ariaLabel={`${label} input args`} value={args} onChange={() => undefined} width={180} />
    </div>
  );

  return (
    <div className="sqd-tab-content">
      <SqdFieldset legend={<span>Custom analysis <SqdHelpLink url="https://strategyquant.com/doc/strategyquant/custom-analysis" /></span>}>
        <label className="sqd-label">Performs the specified custom analysis on all strategies of given databank</label>
        <br />
        {row('Per strategy analysis', customAnalysisDefaults.perStrategy1, perStrategy, customAnalysisDefaults.inputArgsPerStrategy1, 'ps1')}
        {row('Full databank analysis', customAnalysisDefaults.fullDatabank1, fullDatabank, customAnalysisDefaults.inputArgsFullDatabank1, 'fd1')}
        {row('Per strategy analysis', customAnalysisDefaults.perStrategy2, perStrategy, customAnalysisDefaults.inputArgsPerStrategy2, 'ps2')}
        {row('Full databank analysis', customAnalysisDefaults.fullDatabank2, fullDatabank, customAnalysisDefaults.inputArgsFullDatabank2, 'fd2')}
        <div className="sqd-ca-row">
          <label className="sqd-label" style={{ textAlign: 'right' }}>Source</label>
          <SqdSelect
            ariaLabel="Databank source"
            value={customAnalysisDefaults.source}
            onChange={() => undefined}
            options={customAnalysisDefaults.availableDatabanks.map(d => ({ value: d, label: d }))}
            width={170}
          />
          <label className="sqd-label" style={{ width: 'auto' }}>Destination</label>
          <SqdSelect
            ariaLabel="Databank destination"
            value={customAnalysisDefaults.availableDatabanks[0]}
            onChange={() => undefined}
            options={customAnalysisDefaults.availableDatabanks.map(d => ({ value: d, label: d }))}
            width={170}
          />
        </div>
      </SqdFieldset>
    </div>
  );
}
