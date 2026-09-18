export type DataSourceDialogId =
  | 'new-instrument'
  | 'dukascopy-add'
  | 'dukascopy-download'
  | 'dukascopy-information'
  | 'tickdownloader-import'
  | 'file-add'
  | 'file-import'
  | 'file-mass-import'
  | 'file-application-import'
  | 'sq-equity-find'
  | 'sq-futures-find'
  | 'darwinex-add'
  | 'darwinex-import'
  | 'darwinex-download'
  | 'crypto-add'
  | 'crypto-download'
  | 'yahoo-add'
  | 'yahoo-download'
  | 'mt5-import'
  | 'mass-delete'
  | 'save-definitions'
  | 'load-definitions'
  | 'instrument-identification'
  | 'data-format-name'
  | 'data-usage-conditions'
  | 'dependency-warning';

export type DirectDataSourceAction =
  | 'sq-equity-update'
  | 'sq-futures-update'
  | 'update-all'
  | 'update-selected';

export type DataSourceCommandIcon =
  | 'add'
  | 'application-import'
  | 'binance'
  | 'bitfinex'
  | 'coinbase'
  | 'coin-m'
  | 'crypto'
  | 'download'
  | 'file-import'
  | 'folder-import'
  | 'information'
  | 'mass-import'
  | 'poloniex'
  | 'refresh'
  | 'search'
  | 'symbol-list'
  | 'terminal-import'
  | 'usdt-m';

export interface DataSourceCommand {
  id: string;
  label: string;
  icon: DataSourceCommandIcon;
  dialog?: DataSourceDialogId;
  action?: DirectDataSourceAction;
  exchange?: string;
  children?: readonly DataSourceCommand[];
}

export interface DataSourceProvider {
  id: string;
  label: string;
  commands: readonly DataSourceCommand[];
}

export interface DataSourceContextAction {
  id: string;
  label: string;
  dialog?: DataSourceDialogId;
  action?: DirectDataSourceAction;
  requiresSelection?: boolean;
}

const cryptoExchanges = [
  ['binance', 'Binance spot', 'binance'],
  ['binance-coin-m', 'Binance Coin-M', 'coin-m'],
  ['binance-usdt-m', 'Binance USDT-M', 'usdt-m'],
  ['bitfinex', 'Bitfinex', 'bitfinex'],
  ['poloniex', 'Poloniex', 'poloniex'],
  ['coinbase-pro', 'Coinbase Pro', 'coinbase'],
] as const;

export const dataSourceProviders: readonly DataSourceProvider[] = [
  {
    id: 'dukascopy',
    label: 'Dukascopy data',
    commands: [
      { id: 'dukascopy-add', label: 'Add new Dukascopy symbol', icon: 'add', dialog: 'dukascopy-add' },
      { id: 'dukascopy-download', label: 'Download data for existing symbol', icon: 'download', dialog: 'dukascopy-download' },
      { id: 'dukascopy-information', label: 'View data usage information', icon: 'information', dialog: 'dukascopy-information' },
    ],
  },
  {
    id: 'tickdownloader',
    label: 'TickDownloader import',
    commands: [{ id: 'tickdownloader-import', label: 'Import TickDownloader data', icon: 'folder-import', dialog: 'tickdownloader-import' }],
  },
  {
    id: 'file-import',
    label: 'File import',
    commands: [
      { id: 'file-add', label: 'Add data symbol', icon: 'add', dialog: 'file-add' },
      { id: 'file-import', label: 'Import one data file', icon: 'file-import', dialog: 'file-import' },
      { id: 'file-mass-import', label: 'Import multiple files from a folder', icon: 'mass-import', dialog: 'file-mass-import' },
      { id: 'file-application-import', label: 'Import application data', icon: 'application-import', dialog: 'file-application-import' },
    ],
  },
  {
    id: 'sq-equity',
    label: 'SQ Equity data',
    commands: [
      { id: 'sq-equity-find', label: 'Find and add equity data', icon: 'search', dialog: 'sq-equity-find' },
      { id: 'sq-equity-update', label: 'Update SQ Equity datasets', icon: 'refresh', action: 'sq-equity-update' },
    ],
  },
  {
    id: 'sq-futures',
    label: 'SQ Futures data',
    commands: [
      { id: 'sq-futures-find', label: 'Find and add futures data', icon: 'search', dialog: 'sq-futures-find' },
      { id: 'sq-futures-update', label: 'Update SQ Futures datasets', icon: 'refresh', action: 'sq-futures-update' },
    ],
  },
  {
    id: 'darwinex',
    label: 'Darwinex Tick Data',
    commands: [
      { id: 'darwinex-add', label: 'Add Darwinex data', icon: 'add', dialog: 'darwinex-add' },
      { id: 'darwinex-import', label: 'Import data from a Darwinex folder', icon: 'folder-import', dialog: 'darwinex-import' },
      { id: 'darwinex-download', label: 'Download data for existing symbols', icon: 'download', dialog: 'darwinex-download' },
    ],
  },
  {
    id: 'crypto',
    label: 'Crypto data',
    commands: [
      {
        id: 'crypto-add',
        label: 'Add crypto symbol',
        icon: 'crypto',
        children: cryptoExchanges.map(([id, label, icon]) => ({
          id: `crypto-add-${id}`,
          label,
          icon,
          dialog: 'crypto-add' as const,
          exchange: label,
        })),
      },
      { id: 'crypto-download', label: 'Download data for existing symbol', icon: 'download', dialog: 'crypto-download' },
    ],
  },
  {
    id: 'yahoo',
    label: 'Yahoo data',
    commands: [
      { id: 'yahoo-add', label: 'Add Yahoo symbols', icon: 'symbol-list', dialog: 'yahoo-add' },
      { id: 'yahoo-download', label: 'Download data for existing symbol', icon: 'download', dialog: 'yahoo-download' },
    ],
  },
  {
    id: 'mt5',
    label: 'MT5 import',
    commands: [{ id: 'mt5-import', label: 'Import data from MetaTrader 5', icon: 'terminal-import', dialog: 'mt5-import' }],
  },
] as const;

export const dataSourceContextActions: readonly DataSourceContextAction[] = [
  { id: 'update-all', label: 'Update all', action: 'update-all' },
  { id: 'update-selected', label: 'Update selected', action: 'update-selected', requiresSelection: true },
  { id: 'mass-delete', label: 'Mass delete', dialog: 'mass-delete', requiresSelection: true },
  { id: 'save-definitions', label: 'Save', dialog: 'save-definitions', requiresSelection: true },
  { id: 'load-definitions', label: 'Load', dialog: 'load-definitions' },
] as const;
