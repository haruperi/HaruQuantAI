import { useOptionsController } from '../OptionsCtrl';
import { SqdFieldset, SqdSelect, SqdSpinner } from '../../ProjectWorkbench/settings/SettingsControls';
import { formatTimeOfDay } from '../../ProjectWorkbench/settings/sharedSettingsFixtures';

/** "Trading options" tab (donor evidence SQX144-EV-000041): the property grid. */
export function TradingOptionsTab() {
  const { properties, setProperty } = useOptionsController();

  return (
    <div id="optionsTab" className="sqd-tab-content">
      <SqdFieldset legend="Build and Trading Options">
        <div className="sqd-prop-grid" role="table" aria-label="Build and trading options">
          {properties.map(property => (
            <div className="sqd-prop-row" role="row" key={property.key}>
              <label className="sqd-label" role="cell">{property.label}</label>
              <div className="sqd-prop-control" role="cell">
                {property.type === 'checkbox' && (
                  <span className={`sqd-switch${property.value ? ' on' : ''}`} title={property.label}>
                    <input type="checkbox" checked={Boolean(property.value)} onChange={e => setProperty(property.key, e.target.checked)} />
                    <i />
                  </span>
                )}
                {property.type === 'spinner' && (
                  <SqdSpinner ariaLabel={property.label} value={Number(property.value)} min={0} max={100} onChange={v => setProperty(property.key, v)} />
                )}
                {property.type === 'time' && (
                  <SqdSelect
                    ariaLabel={property.label}
                    value={String(property.value)}
                    onChange={v => setProperty(property.key, Number(v))}
                    options={[0, 3600, 7200, 10800, 14400, 18000, 21600, 25200, 28800, 32400, 36000, 39600, 43200, 46800, 50400, 54000, 57600, 61200, 64800, 68400, 72000, 75600, 79200, 82800, 86400].map(s => ({ value: String(s), label: formatTimeOfDay(s) }))}
                    width={100}
                  />
                )}
                {property.type === 'select' && property.options && (
                  <SqdSelect
                    ariaLabel={property.label}
                    value={String(property.value)}
                    onChange={v => setProperty(property.key, v)}
                    options={property.options.map(o => ({ value: o, label: o }))}
                    width={160}
                  />
                )}
              </div>
            </div>
          ))}
        </div>
      </SqdFieldset>
    </div>
  );
}
