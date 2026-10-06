import type { AddPopupController } from './addPopupCtrl';

export function SelectInstrumentsPopup({ controller }: { controller: AddPopupController }) {
  const { activeBroker, mapping, selected, setMapping } = controller;
  if (!mapping) return null;
  return (
    <section className="dukas-panel dukas-mapping">
      <strong>You have chosen broker profile {activeBroker?.name}</strong>
      <p>Downloaded data will be recomputed to this broker timezone.</p>
      <strong>Please select corresponding instrument for added data</strong>
      <p>
        Select a corresponding broker profile instrument for every symbol. If one is not defined,
        skip the symbol or use the Default instrument.
      </p>
      <p>Mass action</p>
      <div>
        Set all unconfigured symbols to{' '}
        <button
          onClick={() =>
            setMapping(
              Object.fromEntries(
                Object.entries(mapping).map(([key, value]) => [
                  key,
                  value === '-1001' ? '-1' : value,
                ]),
              ),
            )
          }
        >
          Default instrument
        </button>{' '}
        <button
          onClick={() =>
            setMapping(
              Object.fromEntries(
                Object.entries(mapping).map(([key, value]) => [
                  key,
                  value === '-1001' ? '-1000' : value,
                ]),
              ),
            )
          }
        >
          Skip adding the symbol
        </button>
      </div>
      <div className="dukas-grid">
        <table aria-label="Instrument mappings">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Instrument</th>
            </tr>
          </thead>
          <tbody>
            {selected.map((symbol) => (
              <tr key={symbol}>
                <td>{symbol}</td>
                <td>
                  <select
                    aria-label={`Instrument for ${symbol}`}
                    value={mapping[symbol]}
                    onChange={(event) => setMapping({ ...mapping, [symbol]: event.target.value })}
                  >
                    <option value="-1001">choose instrument</option>
                    {activeBroker?.instruments
                      .filter((item) => !item.startsWith('['))
                      .map((item) => (
                        <option key={item}>{item}</option>
                      ))}
                    <option value="-1">Default</option>
                    <option value="-1000">Skip adding this symbol</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
