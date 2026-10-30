import { useCallback, useEffect, useRef, useState } from 'react';
import { Button } from '../../common/components/ui';
import { GridTestRows, type GridTestRow } from './rows';

export const GRID_TEST_COLUMNS = ['Index', 'Multiplier (x2)', 'Text'] as const;

export function GridTestWorkspace() {
  const [rows, setRows] = useState<GridTestRow[]>(() => GridTestRows.manual_batch());
  const [selectedIds, setSelectedIds] = useState<Set<number>>(() => new Set());
  const [testRunning, setTestRunning] = useState<boolean>(false);

  const timedCounterRef = useRef<number>(1);
  const rowsRef = useRef<GridTestRow[]>(rows);
  rowsRef.current = rows;

  // Manual batch addition
  const handleAdd100Rows = useCallback(() => {
    const newBatch = GridTestRows.manual_batch();
    setRows(prev => [...prev, ...newBatch]);
  }, []);

  // Selection handlers
  const handleSelectAll = useCallback(() => {
    setSelectedIds(new Set(rowsRef.current.map(r => r[0])));
  }, []);

  const handleSelectNone = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  // Clear handler
  const handleClear = useCallback(() => {
    setTestRunning(false);
    setRows([]);
    setSelectedIds(new Set());
  }, []);

  // Toggle single row selection
  const handleRowClick = useCallback((id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  // Automated stress test timer loop
  useEffect(() => {
    if (!testRunning) {
      return;
    }

    const intervals = GridTestRows.intervals_ms();

    // 1. Add timer (20ms): insert timed row
    const addTimer = window.setInterval(() => {
      const { row, next_counter } = GridTestRows.timed_row(timedCounterRef.current);
      timedCounterRef.current = next_counter;
      setRows(prev => [...prev, row]);
    }, intervals.add);

    // 2. Remove timer (30ms): remove oldest row if exists
    const removeTimer = window.setInterval(() => {
      setRows(prev => (prev.length > 0 ? prev.slice(1) : prev));
    }, intervals.remove);

    // 3. Change timer (40ms): mutate a row if exists
    const changeTimer = window.setInterval(() => {
      setRows(prev => {
        if (prev.length === 0) return prev;
        const targetIdx = prev.length - 1;
        const target = prev[targetIdx];
        const updated: GridTestRow = [target[0], target[1] + 1, `${target[0]}-modified`];
        const next = [...prev];
        next[targetIdx] = updated;
        return next;
      });
    }, intervals.change);

    return () => {
      window.clearInterval(addTimer);
      window.clearInterval(removeTimer);
      window.clearInterval(changeTimer);
    };
  }, [testRunning]);

  return (
    <section className="header-app grid-test sq-app-home" aria-labelledby="grid-test-title">
      <header className="header-app-title">
        <div>
          <h1 id="grid-test-title">Grid test</h1>
          <span>UI data-grid exercise and stress-test harness</span>
        </div>
      </header>

      <div className="infoPanel" data-testid="info-panel">
        <label>
          Rows in grid: <span className="rows-count" data-testid="rows-count">{rows.length}</span>
        </label>
        <span className="selected-count">
          Selected: {selectedIds.size}
        </span>
      </div>

      <div
        id="testGrid"
        className="plain-table-wrap"
        data-testid="test-grid"
        style={{ width: '600px', height: '360px', margin: '0 auto', overflowY: 'auto' }}
      >
        <table className="plain-table grid-test-table">
          <thead>
            <tr>
              <th style={{ width: '48px' }}>Select</th>
              <th>Index</th>
              <th>Multiplier (x2)</th>
              <th>Text</th>
            </tr>
          </thead>
          <tbody>
            {rows.length > 0 ? (
              rows.map((row, idx) => {
                const isSelected = selectedIds.has(row[0]);
                return (
                  <tr
                    key={`${row[0]}-${idx}`}
                    className={isSelected ? 'grid-row-selected selected' : ''}
                    onClick={() => handleRowClick(row[0])}
                    style={{ cursor: 'pointer' }}
                  >
                    <td>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleRowClick(row[0])}
                        aria-label={`Select row ${row[0]}`}
                      />
                    </td>
                    <td>{row[0]}</td>
                    <td>{row[1]}</td>
                    <td>{row[2]}</td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={4} className="grid-empty text-center py-4">
                  No rows in test grid. Click &quot;Add 100 rows&quot; or &quot;Start test&quot;.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="controlPanel flex items-center justify-center gap-3 mt-4" data-testid="control-panel">
        <Button
          id="buttonStartStopTest-64a"
          className={testRunning ? 'danger' : 'primary'}
          onClick={() => setTestRunning(prev => !prev)}
        >
          {testRunning ? 'Stop test' : 'Start test'}
        </Button>
        <Button
          id="buttonSelectAll-64b"
          onClick={handleSelectAll}
          disabled={rows.length === 0}
        >
          Select All
        </Button>
        <Button
          id="buttonSelectNone-64c"
          onClick={handleSelectNone}
          disabled={selectedIds.size === 0}
        >
          Select None
        </Button>
        <Button
          id="buttonClear-64d"
          onClick={handleClear}
          disabled={rows.length === 0}
        >
          Clear
        </Button>
        <Button
          id="buttonAdd100Rows-64e"
          onClick={handleAdd100Rows}
        >
          Add 100 rows
        </Button>
      </div>
    </section>
  );
}
