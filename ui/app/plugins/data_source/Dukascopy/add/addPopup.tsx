import { useEffect, useRef } from 'react';
import { categories, filterCatalogue } from '../dukascopy';
import { SelectInstrumentsPopup } from './selectInstrumentsPopup';
import { disclaimer, useAddPopupController, type AddPopupProps } from './addPopupCtrl';
import './styles.css';

export function AddPopup(props: AddPopupProps) {
  const { open, onClose } = props;
  const controller = useAddPopupController(props);
  const {
    saving,
    brokerLoading,
    brokerError,
    brokerInvalid,
    reloadBrokers,
    query,
    category,
    selected,
    dataType,
    broker,
    postfix,
    confirmed,
    error,
    warning,
    mapping,
    brokers,
    rows,
    groups,
    root,
    headerCheck,
    all,
    changeFilter,
    toggle,
    save,
    setMapping,
    setError,
    setConfirmed,
    setDataType,
    setBroker,
    setPostfix,
    setWarning,
  } = controller;
  if (!open) return null;
  return (
    <div className="dukas-overlay">
      <div
        ref={root}
        className="dukas-dialog"
        role="dialog"
        aria-modal="true"
        aria-busy={saving}
        aria-labelledby="dukas-title"
        onKeyDown={(event) => {
          if (event.key === 'Escape') {
            event.stopPropagation();
            if (saving) return;
            onClose();
          }
          if (event.key === 'Tab') {
            const controls = Array.from(
              root.current?.querySelectorAll<HTMLElement>(
                'button:not(:disabled), input:not(:disabled), select:not(:disabled)',
              ) ?? [],
            );
            const first = controls[0];
            const last = controls[controls.length - 1];
            if (event.shiftKey && document.activeElement === first) {
              event.preventDefault();
              last?.focus();
            }
            if (!event.shiftKey && document.activeElement === last) {
              event.preventDefault();
              first?.focus();
            }
          }
        }}
      >
        <header>
          <h2 id="dukas-title">Add Dukascopy data</h2>
          <button disabled={saving} aria-label="Close" onClick={onClose}>
            Ã—
          </button>
        </header>
        <div className="dukas-body" inert={saving}>
          <section className="dukas-panel">
              <strong>Choose from available data</strong>
              <div className="dukas-filters">
                <input
                  aria-label="Filter available symbols"
                  placeholder="Filter items"
                  value={query}
                  onChange={(event) => changeFilter(event.target.value, category)}
                />
                <label>
                  Show types{' '}
                  <select
                    value={category}
                    onChange={(event) => changeFilter(query, event.target.value)}
                  >
                    {categories.map((item) => (
                      <option key={item.value} value={item.value}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="dukas-grid">
                <table aria-label="Available Dukascopy symbols">
                  <colgroup>
                    <col style={{ width: 24 }} />
                    <col style={{ width: 150 }} />
                    <col style={{ width: 200 }} />
                    <col style={{ width: 200 }} />
                    <col style={{ width: 200 }} />
                  </colgroup>
                  <thead>
                    <tr>
                      <th>
                        <input
                          ref={headerCheck}
                          type="checkbox"
                          aria-label="Select all available symbols"
                          checked={all}
                          disabled={!rows.length}
                          onChange={() => toggle(rows.map((row) => row.symbol))}
                        />
                      </th>
                      <th>Symbol</th>
                      <th>Name</th>
                      <th>Available M1 data range</th>
                      <th>Available Tick data range</th>
                    </tr>
                  </thead>
                  <tbody>
                    {groups.map((group) => (
                      <Group key={group.name} group={group} selected={selected} toggle={toggle} />
                    ))}
                    {!rows.length && (
                      <tr>
                        <td colSpan={5}>No Dukascopy symbols available.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              <div className="dukas-options">
                <strong>Data type</strong>
                <label>
                  <input
                    type="radio"
                    name="dukas-type"
                    checked={dataType === 'TICK'}
                    onChange={() => setDataType('TICK')}
                  />{' '}
                  Tick data
                </label>
                <label>
                  <input
                    type="radio"
                    name="dukas-type"
                    checked={dataType === 'M1'}
                    onChange={() => setDataType('M1')}
                  />{' '}
                  M1 data
                </label>
              </div>
              <div className="dukas-settings">
                <label>
                  <strong>Broker profile *</strong>
                  <select
                    aria-label="Broker profile *"
                    aria-describedby="dukas-broker-status"
                    aria-busy={brokerLoading}
                    disabled={brokerLoading || !!brokerError}
                    value={broker}
                    onChange={(event) => {
                      const id = event.target.value;
                      setBroker(id);
                      setPostfix(brokers.find((item) => item.id === id)?.postfix ?? '');
                      setWarning(id !== '-1');
                      setError('');
                    }}
                  >
                    <option value="-1">Default</option>
                    {brokerInvalid && !brokers.some(item => item.id === broker) && (
                      <option value={broker} disabled>Previously selected broker is unavailable</option>
                    )}
                    {brokers.map(item => (
                      <option key={item.id} value={item.id} disabled={!item.mtUse}>
                        {item.name.startsWith('[[') && item.name.endsWith(']]') ? item.name.slice(2, -2).trim() : item.name}{item.mtUse ? '' : ' (disabled for data management)'}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <strong>Data postfix</strong>
                  <span>
                    <input value={postfix} onChange={(event) => setPostfix(event.target.value)} />
                    <small>This postfix will be optionally added to the data names created</small>
                  </span>
                </label>
              </div>
              <div id="dukas-broker-status">
                {brokerLoading ? <p role="status">Loading broker profiles...</p>
                  : brokerError ? <p className="dukas-error" role="alert">{brokerError}{' '}
                    <button className="sq-button" onClick={() => { setError(''); void reloadBrokers(); }}>Retry broker profiles</button>
                  </p>
                  : brokerInvalid ? <p className="dukas-error" role="alert">The selected broker is no longer available for data management. Choose another profile.</p>
                  : !brokers.length ? <p role="status">No saved broker profiles. Default is available.</p> : null}
              </div>
              {warning && !brokerInvalid && (

                <p className="dukas-warning" role="status">
                  You have selected a non-default broker. Data will be automatically adjusted to the
                  broker's time zone during download.
                </p>
              )}
            </section>
        </div>
        <footer>
          <label className="dukas-consent">
            <input
              disabled={saving}
              role="switch"
              type="checkbox"
              checked={confirmed}
              onChange={(event) => setConfirmed(event.target.checked)}
            />
            <span>{disclaimer}</span>
          </label>
          {error && (
            <p className="dukas-error" role="alert">
              {error}
            </p>
          )}
          <div className="dukas-actions">
            <button className="dukas-link sq-button" disabled={saving} onClick={onClose}>
              Close
            </button>
            <button className="dukas-save sq-button primary" disabled={saving || brokerLoading || !!brokerError || brokerInvalid} onClick={save}>
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}
function Group({
  group,
  selected,
  toggle,
}: {
  group: { name: string; rows: ReturnType<typeof filterCatalogue> };
  selected: string[];
  toggle: (symbols: string[]) => void;
}) {
  const ref = useRef<HTMLInputElement>(null);
  const count = group.rows.filter((row) => selected.includes(row.symbol)).length;
  useEffect(() => {
    if (ref.current) ref.current.indeterminate = count > 0 && count < group.rows.length;
  }, [count, group.rows.length]);
  return (
    <>
      <tr className="dukas-group">
        <td>
          <input
            ref={ref}
            type="checkbox"
            aria-label={`Select ${group.name}`}
            checked={count === group.rows.length}
            onChange={() => toggle(group.rows.map((row) => row.symbol))}
          />
        </td>
        <td colSpan={4}>{group.name}</td>
      </tr>
      {group.rows.map((row) => (
        <tr key={row.symbol} className={selected.includes(row.symbol) ? 'dukas-selected' : ''}>
          <td>
            <input
              type="checkbox"
              aria-label={`Select symbol ${row.symbol}`}
              checked={selected.includes(row.symbol)}
              onChange={() => toggle([row.symbol])}
            />
          </td>
          <td>{row.symbol}</td>
          <td>{row.name}</td>
          <td>from {row.dateFromM1.replaceAll('-', '.')}</td>
          <td>from {row.dateFrom.replaceAll('-', '.')}</td>
        </tr>
      ))}
    </>
  );
}
