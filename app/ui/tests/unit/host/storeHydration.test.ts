import { afterEach, describe, expect, it, vi } from 'vitest';

describe('saved Builder settings hydration', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('fills fields absent from an older Builder record without replacing saved values', async () => {
    vi.resetModules();
    const memory = new Map<string, string>([
      [
        'sqx-recreation-v1',
        JSON.stringify({
          state: { module: 'builder', tab: 'settings', builder: { population: 250 } },
          version: 1,
        }),
      ],
    ]);
    const storage = {
      getItem: (key: string) => memory.get(key) ?? null,
      setItem: (key: string, value: string) => memory.set(key, value),
      removeItem: (key: string) => memory.delete(key),
    };
    vi.stubGlobal('window', { localStorage: storage });

    const { useAppStore } = await import('../../../app/host/store');
    await useAppStore.persist.rehydrate();
    const { builder } = useAppStore.getState();

    expect(builder.population).toBe(250);
    expect(builder.customBlocks).toEqual({});
    expect(builder.crossChecks.length).toBeGreaterThan(0);
    expect(builder.mode).toBe('Genetic evolution');
  });
});
