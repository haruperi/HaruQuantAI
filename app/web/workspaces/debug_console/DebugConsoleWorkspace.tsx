import { useCallback, useMemo, useState } from 'react';
import { Select, TextInput } from '../../common/components/ui';
import { useAppStore } from '../../shell/store';
import { DebugLogBuffer, type LogFilter, type LogMessage } from './buffer';

export interface DebugLogEntry {
  id: string;
  time: string;
  category: string;
  message: string;
}

export function parseBufferLines(bufferText: string): DebugLogEntry[] {
  if (!bufferText) return [];
  const rawLines = bufferText.split('</br>').filter(line => line.trim().length > 0);
  return rawLines.map((line, idx) => {
    // Format: time + ' ' + category + ' - ' + message
    const firstSpace = line.indexOf(' ');
    if (firstSpace !== -1) {
      const time = line.slice(0, firstSpace);
      const dashIdx = line.indexOf(' - ', firstSpace + 1);
      if (dashIdx !== -1) {
        const category = line.slice(firstSpace + 1, dashIdx);
        const message = line.slice(dashIdx + 3);
        return {
          id: `log-${idx}-${time}-${category}`,
          time,
          category,
          message,
        };
      }
    }
    return {
      id: `log-${idx}`,
      time: '—',
      category: 'General',
      message: line,
    };
  });
}

export function debugCategories(entries: LogMessage[]): string[] {
  const discovered = Array.from(new Set(entries.map(e => e.category)));
  return ['all', ...discovered.filter(c => c !== 'all')];
}

export function buildInitialLogs(notifications: string[]): LogMessage[] {
  const time = '16:00:00';
  const systemLogs: LogMessage[] = [
    { time, category: 'System', message: 'Diagnostic debug console initialized.' },
    { time, category: 'Engine', message: 'Core runtime listener attached.' },
  ];
  const noticeLogs: LogMessage[] = notifications.map((n, idx) => ({
    time: `16:00:${String(idx + 2).padStart(2, '0')}`,
    category: 'Application',
    message: n,
  }));
  return [...systemLogs, ...noticeLogs];
}

export function DebugConsoleWorkspace() {
  const notifications = useAppStore(s => s.notifications);

  const [category, setCategory] = useState<string>('all');
  const [query, setQuery] = useState<string>('');
  const [cleared, setCleared] = useState<boolean>(false);

  const initialLogs = useMemo(() => buildInitialLogs(notifications), [notifications]);
  const categories = useMemo(() => debugCategories(initialLogs), [initialLogs]);

  // Compute buffer state with case-sensitive filtering
  const visibleEntries = useMemo(() => {
    if (cleared) {
      return [];
    }
    const buffer = new DebugLogBuffer();
    const filter: LogFilter = { category, text: query };
    buffer.filter = filter;
    buffer.receive(initialLogs);
    return parseBufferLines(buffer.text);
  }, [cleared, initialLogs, category, query]);

  const handleClear = useCallback(() => {
    setCleared(true);
  }, []);

  return (
    <section className="header-app debug-console" aria-labelledby="debug-console-title">
      <header className="header-app-title">
        <div>
          <h1 id="debug-console-title">Debug Console</h1>
          <span>Application diagnostic log</span>
        </div>
      </header>

      <div className="debug-toolbar" data-testid="debug-toolbar">
        <label>
          Category
          <Select value={category} onChange={setCategory}>
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </Select>
        </label>
        <label>
          Filter
          <TextInput
            value={query}
            onChange={event => setQuery(event.target.value)}
            placeholder="Filter messages (case-sensitive)"
          />
        </label>
      </div>

      <div className="debug-log" role="log" aria-live="polite" data-testid="debug-log">
        {visibleEntries.length > 0 ? (
          visibleEntries.map(entry => (
            <div key={entry.id} className="debug-log-entry">
              <time>{entry.time}</time>
              <strong>{entry.category}</strong>
              <span>- {entry.message}</span>
            </div>
          ))
        ) : (
          <p className="debug-empty" data-testid="debug-empty">
            No log entries match the current filter.
          </p>
        )}
      </div>

      <button
        className="clear-debug-log"
        data-testid="clear-debug-log"
        onClick={handleClear}
        disabled={visibleEntries.length === 0}
      >
        Clear log
      </button>
    </section>
  );
}
