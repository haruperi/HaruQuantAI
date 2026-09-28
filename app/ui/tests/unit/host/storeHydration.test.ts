import { afterEach, describe, expect, it, vi } from 'vitest';

describe('host shell hydration', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('restores view selections while ignoring domain state in a legacy record', async () => {
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
    vi.stubGlobal('localStorage', storage);

    const { useAppStore } = await import('../../../app/host/store');
    await useAppStore.persist.rehydrate();
    const state = useAppStore.getState();
    expect(state.module).toBe('builder');
    expect(state.tab).toBe('settings');
    expect('builder' in state).toBe(false);
    expect(typeof state.setModule).toBe('function');
  });
});
