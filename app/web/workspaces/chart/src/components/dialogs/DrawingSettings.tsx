import { useStore } from 'zustand';
import { useChart } from '../../hooks/useChartEngine';
import { keyFor, type Drawing } from '../../types';
import { tools } from '../../tools/catalog';
import { Modal } from '../Modal';
export function DrawingSettings() {
  const { store } = useChart(),
    s = useStore(store),
    list = s.drawings[keyFor(s.chart)] ?? [],
    drawing = list.find((d) => d.id === s.ui.selected);
  if (!drawing)
    return (
      <Modal title="Drawing settings">
        <p className="cq-form">Select a drawing first.</p>
      </Modal>
    );
  const update = (change: Partial<Drawing>) =>
    s.setDrawings(list.map((d) => (d.id === drawing.id ? { ...d, ...change } : d)));
  return (
    <Modal title={tools[drawing.tool].label + ' settings'}>
      <div className="cq-form">
        <div className="cq-fields">
          <label>
            Color
            <input
              type="color"
              value={drawing.color}
              onChange={(e) => update({ color: e.target.value })}
            />
          </label>
          <label>
            Line width
            <input
              type="number"
              min="1"
              max="8"
              value={drawing.width}
              onChange={(e) =>
                update({ width: Math.max(1, Math.min(8, Number(e.target.value) || 1)) })
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
              value={drawing.opacity}
              onChange={(e) => update({ opacity: Number(e.target.value) })}
            />
          </label>
          <label>
            Line style
            <select
              value={drawing.dash ? 'dashed' : 'solid'}
              onChange={(e) => update({ dash: e.target.value === 'dashed' })}
            >
              <option value="solid">Solid</option>
              <option value="dashed">Dashed</option>
            </select>
          </label>
        </div>
        {(drawing.tool === 'LongPosition' || drawing.tool === 'ShortPosition') && (
          <div className="cq-fields">
            <label>
              Account size
              <input
                aria-label="Position account size"
                type="number"
                min="0.01"
                max="1000000000000"
                value={drawing.positionSizing?.accountSize ?? 1000}
                onChange={(e) => {
                  const value = Number(e.target.value);
                  if (Number.isFinite(value) && value > 0 && value <= 1e12)
                    update({
                      positionSizing: {
                        accountSize: value,
                        riskPercent: drawing.positionSizing?.riskPercent ?? 1,
                      },
                    });
                }}
              />
            </label>
            <label>
              Risk (%)
              <input
                aria-label="Position risk percent"
                type="number"
                min="0.01"
                max="100"
                step="0.1"
                value={drawing.positionSizing?.riskPercent ?? 1}
                onChange={(e) => {
                  const value = Number(e.target.value);
                  if (Number.isFinite(value) && value > 0 && value <= 100)
                    update({
                      positionSizing: {
                        accountSize: drawing.positionSizing?.accountSize ?? 1000,
                        riskPercent: value,
                      },
                    });
                }}
              />
            </label>
          </div>
        )}
        <label>
          {drawing.tool === 'Image' ? 'Image URL (HTTPS or HTTP)' : drawing.tool === 'Table' ? 'Table cells (pipe-separated columns)' : 'Text label'}
          {drawing.tool === 'Image' ? (
            <input
              type="url"
              aria-label="Image URL"
              placeholder="https://example.com/chart.png"
              value={drawing.text}
              onChange={(e) => update({ text: e.target.value })}
            />
          ) : ['Note', 'PriceNote', 'Table', 'Callout', 'Comment', 'Post', 'Idea'].includes(drawing.tool) ? (
            <textarea
              aria-label="Drawing text"
              rows={drawing.tool === 'Table' ? 5 : 4}
              placeholder={drawing.tool === 'Table' ? 'Field | Value\nPrice | 123.45' : 'Enter annotation text'}
              value={drawing.text}
              onChange={(e) => update({ text: e.target.value })}
            />
          ) : (
            <input
              aria-label="Drawing text"
              value={drawing.text}
              onChange={(e) => update({ text: e.target.value })}
            />
          )}
        </label>
        {drawing.tool === 'TrendLine' && (
          <>
            <label className="cq-check">
              <input
                type="checkbox"
                checked={drawing.extendLeft}
                onChange={(e) => update({ extendLeft: e.target.checked })}
              />
              Extend left
            </label>
            <label className="cq-check">
              <input
                type="checkbox"
                checked={drawing.extendRight}
                onChange={(e) => update({ extendRight: e.target.checked })}
              />
              Extend right
            </label>
          </>
        )}
        <label className="cq-check">
          <input
            type="checkbox"
            checked={drawing.locked}
            onChange={(e) => update({ locked: e.target.checked })}
          />
          Locked
        </label>
        <label className="cq-check">
          <input
            type="checkbox"
            checked={drawing.hidden}
            onChange={(e) => update({ hidden: e.target.checked })}
          />
          Hidden
        </label>
        <button
          className="cq-danger"
          disabled={drawing.locked || s.ui.lock}
          onClick={() => {
            s.setDrawings(list.filter((d) => d.id !== drawing.id));
            s.setUI({ dialog: null, selected: null });
          }}
        >
          Delete drawing
        </button>
      </div>
    </Modal>
  );
}
