import { beforeEach, describe, expect, it } from 'vitest';
import { useAppStore } from '../../../../app/host/store';
import type { ExtensionFile } from '../../../../app/host/types';

describe('Code Editor & Extensions Studio', () => {
  beforeEach(() => {
    useAppStore.getState().reset();
  });

  it('populates initial extensions across all 6 StrategyQuant X categories', () => {
    const store = useAppStore.getState();
    const files = store.extensionFiles;
    expect(files.length).toBeGreaterThanOrEqual(6);

    const categories = new Set(files.map(f => f.category));
    expect(categories.has('Snippets')).toBe(true);
    expect(categories.has('Blocks')).toBe(true);
    expect(categories.has('Indicators')).toBe(true);
    expect(categories.has('Columns')).toBe(true);
    expect(categories.has('CustomAnalysis')).toBe(true);
    expect(categories.has('ResultsPlugins')).toBe(true);

    // Verify presence of specific reference extensions
    const keltner = files.find(f => f.name === 'KeltnerChannel.java');
    expect(keltner).toBeDefined();
    expect(keltner?.content).toContain('class KeltnerChannel extends Indicator');
    expect(keltner?.content).toContain('@Parameter(name = "Period"');
  });

  it('tracks dirty states on content update and clears dirty on save', () => {
    const store = useAppStore.getState();
    const file = store.extensionFiles[0];

    expect(file.dirty).toBeFalsy();

    // Edit content
    store.updateFileContent(file.id, file.content + '\n// Modified comment');
    let updated = useAppStore.getState().extensionFiles.find(f => f.id === file.id)!;
    expect(updated.dirty).toBe(true);
    expect(updated.content).toContain('// Modified comment');

    // Save file
    store.saveFile(file.id);
    updated = useAppStore.getState().extensionFiles.find(f => f.id === file.id)!;
    expect(updated.dirty).toBe(false);
  });

  it('manages multi-tab file lifecycle (open, switch active, close)', () => {
    const store = useAppStore.getState();
    const file1 = store.extensionFiles[0];
    const file2 = store.extensionFiles[1];

    store.openFile(file1.id);
    store.openFile(file2.id);

    expect(useAppStore.getState().openFileIds).toContain(file1.id);
    expect(useAppStore.getState().openFileIds).toContain(file2.id);
    expect(useAppStore.getState().activeFileId).toBe(file2.id);

    // Switch active tab
    store.setActiveFile(file1.id);
    expect(useAppStore.getState().activeFileId).toBe(file1.id);

    // Close tab
    store.closeFile(file1.id);
    expect(useAppStore.getState().openFileIds).not.toContain(file1.id);
    expect(useAppStore.getState().activeFileId).toBe(file2.id);
  });

  it('adds and removes custom extension files', () => {
    const store = useAppStore.getState();
    const initialCount = store.extensionFiles.length;

    const newExt: ExtensionFile = {
      id: 'ext-test-custom',
      name: 'CustomRsiFilter.java',
      category: 'Blocks',
      language: 'java',
      content: 'public class CustomRsiFilter {}',
      dirty: false,
    };

    store.addExtensionFile(newExt);
    expect(useAppStore.getState().extensionFiles.length).toBe(initialCount + 1);
    expect(useAppStore.getState().activeFileId).toBe('ext-test-custom');
    expect(useAppStore.getState().openFileIds).toContain('ext-test-custom');

    // Delete extension file
    store.deleteExtensionFile('ext-test-custom');
    expect(useAppStore.getState().extensionFiles.some(f => f.id === 'ext-test-custom')).toBe(false);
  });

  it('calculates deterministic indicator test values for price series', () => {
    // Basic test of SMA math used by the indicator tester
    const prices = [1.1000, 1.1020, 1.1010, 1.1050, 1.1070];
    const period = 3;
    const window = prices.slice(prices.length - period);
    const sum = window.reduce((a, b) => a + b, 0);
    const sma = sum / period;

    expect(sma).toBeCloseTo(1.10433, 4);

    const atrApprox = 0.0015;
    const multiplier = 2.0;
    const upperBand = sma + multiplier * atrApprox;
    const lowerBand = sma - multiplier * atrApprox;

    expect(upperBand).toBeGreaterThan(sma);
    expect(lowerBand).toBeLessThan(sma);
  });
});
