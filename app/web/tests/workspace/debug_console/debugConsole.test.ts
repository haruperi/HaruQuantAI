import { describe, expect, it } from 'vitest';
import {
  debugCategories,
  parseBufferLines,
} from '../../../workspaces/debug_console/DebugConsoleWorkspace';
import { DebugLogBuffer, type LogMessage } from '../../../workspaces/debug_console/buffer';

describe('HaruQuantAI debug console workspace migration', () => {
  it('enforces case-sensitive filtering and exact category matches', () => {
    const buffer = new DebugLogBuffer();
    buffer.filter = { category: 'Engine', text: 'Order' };

    const accepted: LogMessage = {
      time: '12:00:00',
      category: 'Engine',
      message: 'Order executed',
    };
    const wrongCase: LogMessage = {
      time: '12:00:01',
      category: 'Engine',
      message: 'order executed',
    };
    const wrongCategory: LogMessage = {
      time: '12:00:02',
      category: 'System',
      message: 'Order executed',
    };

    expect(buffer.accepts(accepted)).toBe(true);
    expect(buffer.accepts(wrongCase)).toBe(false);
    expect(buffer.accepts(wrongCategory)).toBe(false);

    buffer.receive([accepted]);
    expect(buffer.text).toBe('12:00:00 Engine - Order executed</br>');
  });

  it('aborts batch processing on first rejected message', () => {
    const buffer = new DebugLogBuffer();
    buffer.filter = { category: 'all', text: 'match' };

    const batch: LogMessage[] = [
      { time: '1', category: 'A', message: 'match 1' },
      { time: '2', category: 'A', message: 'skip this' },
      { time: '3', category: 'A', message: 'match 3' },
    ];

    buffer.receive(batch);
    // Only message 1 was received; message 2 failed, aborting message 3
    expect(buffer.text).toBe('1 A - match 1</br>');
    expect(buffer.text).not.toContain('match 3');
  });

  it('preserves filter on clear and parses buffer lines correctly', () => {
    const buffer = new DebugLogBuffer();
    buffer.filter = { category: 'System', text: 'ready' };
    buffer.receive([{ time: '10:00:00', category: 'System', message: 'ready now' }]);

    const parsed = parseBufferLines(buffer.text);
    expect(parsed).toHaveLength(1);
    expect(parsed[0].time).toBe('10:00:00');
    expect(parsed[0].category).toBe('System');
    expect(parsed[0].message).toBe('ready now');

    buffer.clear();
    expect(buffer.text).toBe('');
    expect(buffer.filter).toEqual({ category: 'System', text: 'ready' });
    expect(parseBufferLines(buffer.text)).toHaveLength(0);
  });

  it('discovers unique categories with all as first option', () => {
    const entries: LogMessage[] = [
      { time: '1', category: 'Jobs', message: 'm1' },
      { time: '2', category: 'Engine', message: 'm2' },
      { time: '3', category: 'Jobs', message: 'm3' },
    ];
    expect(debugCategories(entries)).toEqual(['all', 'Jobs', 'Engine']);
  });
});
