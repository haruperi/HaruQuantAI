import { afterEach, describe, expect, it, vi } from 'vitest';
import { PreviewResources, ownerViewStorage } from '../../../app/host/resourceClient';

describe('host custody of preview documents', () => {
  afterEach(() => vi.unstubAllGlobals());
  function storage() {
    const values = new Map<string, string>();
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value),
      removeItem: (key: string) => values.delete(key),
    });
    return values;
  }
  it('keeps one durable revision readable after producer state and cache restart', () => {
    const values = storage();
    const producer = new PreviewResources();
    const first = producer.read('test.resource', { value: 1 });
    const second = producer.publish('test.resource', { value: 2 }, first.revision);
    const consumer = new PreviewResources();
    expect(consumer.read('test.resource', null)).toEqual(second);
    expect(values.size).toBe(1);
    expect(() => producer.publish('test.resource', {}, first.revision)).toThrow('revision conflict');
    expect(consumer.read('test.resource', null)).toEqual(second);
  });
  it('preserves legacy stored data when saving a new owner view', () => {
    const values = storage();
    values.set('sqx-recreation-v1', 'legacy data');
    expect(ownerViewStorage.getItem('test.owner')).toBe('legacy data');
    ownerViewStorage.setItem('test.owner', 'local view');
    expect(values.get('sqx-recreation-v1')).toBe('legacy data');
    expect(ownerViewStorage.getItem('test.owner')).toBe('local view');
  });
  it('rejects corrupt persisted envelopes without replacing them', () => {
    const values = storage();
    values.set('host.preview.resource.bad', '{"json":42}');
    expect(() => new PreviewResources().read('bad', [])).toThrow('Invalid saved preview resource');
    expect(values.get('host.preview.resource.bad')).toBe('{"json":42}');
  });
});
