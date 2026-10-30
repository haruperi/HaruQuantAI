import { useState } from 'react';
import { useStore } from 'zustand';
import { useChart } from '../../hooks/useChartEngine';
import { indicatorIds, uid, type Indicator } from '../../types';
import { indicators } from '../../indicators/catalog';
import { Modal } from '../Modal';
export function IndicatorsDialog() {
  const { store } = useChart(),
    s = useStore(store),
    [query, setQuery] = useState(''),
    [tab, setTab] = useState('Browse');
  const update = (id: string, change: Partial<Indicator>) =>
    s.setIndicators(s.indicators.map((i) => (i.id === id ? { ...i, ...change } : i)));
  return (
    <Modal title="Indicators">
      <div className="cq-tabs">
        {['Browse', 'Settings'].map((t) => (
          <button key={t} className={t === tab ? 'cq-active' : ''} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>
      {tab === 'Browse' ? (
        <>
          <input
            className="cq-search-input"
            aria-label="Search indicators"
            placeholder="Search indicators…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="cq-indicator-list">
            {indicatorIds
              .filter((id) =>
                (id + indicators[id].name).toLowerCase().includes(query.toLowerCase()),
              )
              .map((id) => (
                <button
                  key={id}
                  onClick={() =>
                    s.setIndicators([
                      ...s.indicators,
                      {
                        id: uid(),
                        kind: id,
                        period: indicators[id].period,
                        slow: 26,
                        signal: id === 'MACD' ? 9 : 3,
                        deviation: 2,
                        color: '#f5a623',
                        width: 1.5,
                        opacity: 1,
                      },
                    ])
                  }
                >
                  <strong>{id}</strong>
                  <span>{indicators[id].name}</span>
                  <small>+ Add</small>
                </button>
              ))}
          </div>
          <p className="cq-muted">
            {s.indicators.length} active indicators · calculations use simulated data.
          </p>
        </>
      ) : (
        <div className="cq-form">
          {!s.indicators.length && <p>Add an indicator from Browse.</p>}
          {s.indicators.map((i) => (
            <fieldset key={i.id}>
              <legend>{i.kind}</legend>
              <div className="cq-fields">
                {!['VWAP', 'Volume'].includes(i.kind) && (
                  <label>
                    Period
                    <input
                      type="number"
                      min="1"
                      max="500"
                      value={i.period}
                      onChange={(e) =>
                        update(i.id, {
                          period: Math.max(
                            1,
                            Math.min(500, Math.round(Number(e.target.value) || 1)),
                          ),
                        })
                      }
                    />
                  </label>
                )}
                {i.kind === 'MACD' && (
                  <label>
                    Slow period
                    <input
                      type="number"
                      min="2"
                      value={i.slow}
                      onChange={(e) =>
                        update(i.id, {
                          slow: Math.max(
                            2,
                            Math.min(500, Math.round(Number(e.target.value) || 26)),
                          ),
                        })
                      }
                    />
                  </label>
                )}
                {['MACD', 'Stochastic'].includes(i.kind) && (
                  <label>
                    Signal period
                    <input
                      type="number"
                      min="1"
                      value={i.signal}
                      onChange={(e) =>
                        update(i.id, {
                          signal: Math.max(
                            1,
                            Math.min(500, Math.round(Number(e.target.value) || 3)),
                          ),
                        })
                      }
                    />
                  </label>
                )}
                {i.kind === 'BollingerBands' && (
                  <label>
                    Deviation
                    <input
                      type="number"
                      min=".1"
                      step=".1"
                      value={i.deviation}
                      onChange={(e) =>
                        update(i.id, { deviation: Math.max(0.1, Number(e.target.value) || 2) })
                      }
                    />
                  </label>
                )}
                <label>
                  Color
                  <input
                    type="color"
                    value={i.color}
                    onChange={(e) => update(i.id, { color: e.target.value })}
                  />
                </label>
                <label>
                  Width
                  <input
                    type="number"
                    min=".5"
                    max="5"
                    step=".5"
                    value={i.width}
                    onChange={(e) =>
                      update(i.id, {
                        width: Math.max(0.5, Math.min(5, Number(e.target.value) || 1)),
                      })
                    }
                  />
                </label>
                <label>
                  Opacity
                  <input
                    type="range"
                    min=".1"
                    max="1"
                    step=".1"
                    value={i.opacity}
                    onChange={(e) => update(i.id, { opacity: Number(e.target.value) })}
                  />
                </label>
              </div>
              <button
                className="cq-danger"
                onClick={() => s.setIndicators(s.indicators.filter((v) => v.id !== i.id))}
              >
                Remove {i.kind}
              </button>
            </fieldset>
          ))}
        </div>
      )}
    </Modal>
  );
}
