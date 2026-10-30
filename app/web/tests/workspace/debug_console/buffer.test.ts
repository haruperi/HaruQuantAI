import { describe, expect, it } from 'vitest';
import { DebugLogBuffer } from '../../../workspaces/debug_console/buffer';

describe('DebugLogBuffer deterministic behavior', () => {
  it('defaults and prepend order', () => {
    const buffer = new DebugLogBuffer();
    expect(buffer.text).toBe('');
    expect(buffer.filter).toEqual({ category: 'all', text: '' });

    buffer.receive([
      { time: '1', category: 'A', message: 'a' },
      { time: '2', category: 'B', message: 'b' },
    ]);
    expect(buffer.text).toBe('2 B - b</br>1 A - a</br>');
  });

  it('first rejected message aborts batch', () => {
    const buffer = new DebugLogBuffer();
    buffer.filter = { category: 'all', text: 'ok' };

    buffer.receive([
      { time: '1', category: 'A', message: 'ok' },
      { time: '2', category: 'A', message: 'no' },
      { time: '3', category: 'A', message: 'ok2' },
    ]);

    expect(buffer.text).toBe('1 A - ok</br>');
    expect(buffer.text).not.toContain('ok2');
  });

  it('case-sensitive filter and clear', () => {
    const buffer = new DebugLogBuffer();
    buffer.filter = { category: 'A', text: 'ok' };

    expect(buffer.accepts({ time: '1', category: 'A', message: 'ok' })).toBe(true);
    expect(buffer.accepts({ time: '2', category: 'A', message: 'OK' })).toBe(false);
    expect(buffer.accepts({ time: '3', category: 'B', message: 'ok' })).toBe(false);

    buffer.receive([{ time: '1', category: 'A', message: 'ok' }]);
    expect(buffer.text).toBe('1 A - ok</br>');

    buffer.clear();
    expect(buffer.text).toBe('');
    expect(buffer.filter).toEqual({ category: 'A', text: 'ok' });
  });

  it('truncate previous buffer before prefix', () => {
    const buffer = new DebugLogBuffer();
    buffer.text = 'x'.repeat(10001);

    buffer.receive([{ time: '1', category: 'A', message: 'a' }]);

    const expected = `1 A - a</br>${'x'.repeat(10000)}`;
    expect(buffer.text).toBe(expected);
    expect(buffer.text.length).toBe('1 A - a</br>'.length + 10000);
  });
});
