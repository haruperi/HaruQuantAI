import { describe, expect, it } from 'vitest';

import { dataSourceContextActions, dataSourceProviders } from './dataSourceRibbon';

describe('Data sources control inventory', () => {
  it('keeps the nine provider controls in their documented order', () => {
    expect(dataSourceProviders.map(provider => provider.id)).toEqual([
      'dukascopy',
      'tickdownloader',
      'file-import',
      'sq-equity',
      'sq-futures',
      'darwinex',
      'crypto',
      'yahoo',
      'mt5',
    ]);
  });

  it('maps every leaf provider command to one dialog or direct action', () => {
    const leaves = dataSourceProviders.flatMap(provider =>
      provider.commands.flatMap(command => command.children ?? [command]),
    );

    expect(leaves).toHaveLength(25);
    for (const command of leaves) {
      expect(Boolean(command.dialog) !== Boolean(command.action)).toBe(true);
    }
  });

  it('lists all supported crypto exchanges explicitly', () => {
    const crypto = dataSourceProviders.find(provider => provider.id === 'crypto');
    const addCommand = crypto?.commands.find(command => command.id === 'crypto-add');

    expect(addCommand?.children?.map(command => command.label)).toEqual([
      'Binance spot',
      'Binance Coin-M',
      'Binance USDT-M',
      'Bitfinex',
      'Poloniex',
      'Coinbase Pro',
    ]);
  });

  it('assigns relevant, varied icons to dropdown commands', () => {
    const fileImport = dataSourceProviders.find(provider => provider.id === 'file-import');
    const crypto = dataSourceProviders.find(provider => provider.id === 'crypto');
    const cryptoAdd = crypto?.commands.find(command => command.id === 'crypto-add');

    expect(new Set(fileImport?.commands.map(command => command.icon)).size).toBe(4);
    expect(new Set(cryptoAdd?.children?.map(command => command.icon)).size).toBe(6);
    for (const provider of dataSourceProviders) {
      for (const command of provider.commands) {
        expect(command.icon).toBeTruthy();
        for (const child of command.children ?? []) expect(child.icon).toBeTruthy();
      }
    }
  });

  it('keeps update operations direct and destructive/file operations dialog-gated', () => {
    expect(dataSourceContextActions).toEqual([
      { id: 'update-all', label: 'Update all', action: 'update-all' },
      { id: 'update-selected', label: 'Update selected', action: 'update-selected', requiresSelection: true },
      { id: 'mass-delete', label: 'Mass delete', dialog: 'mass-delete', requiresSelection: true },
      { id: 'save-definitions', label: 'Save', dialog: 'save-definitions', requiresSelection: true },
      { id: 'load-definitions', label: 'Load', dialog: 'load-definitions' },
    ]);
  });
});
