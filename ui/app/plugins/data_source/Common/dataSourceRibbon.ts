import { yahooProvider } from '../Yahoo/module';
import { tdProvider } from '../TickDownloader/module';
import { equityProvider } from '../SQData/Equity/module';
import { futuresProvider } from '../SQData/Futures/module';
import { mt5Provider } from '../MetaTrader/module';
import { filesProvider } from '../FileImport/module';
import { darwinexProvider } from '../Darwinex/module';
import { cryptoProvider } from '../Crypto/module';
import { dukascopyProvider } from '../Dukascopy/module';

export type DataSourceDialogId =
  | 'new-instrument'
  | 'dukascopy-add'
  | 'dukascopy-download'
  | 'dukascopy-information'
  | 'tickdownloader-import'
  | 'file-add'
  | 'file-import'
  | 'file-mass-import'
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

export const dataSourceProviders: readonly DataSourceProvider[] = [
  dukascopyProvider,
  tdProvider,
  filesProvider,
  equityProvider,
  futuresProvider,
  darwinexProvider,
  cryptoProvider,
  yahooProvider,
  mt5Provider,
] as const;

export const dataSourceContextActions: readonly DataSourceContextAction[] = [
  { id: 'update-all', label: 'Update all', action: 'update-all' },
  { id: 'update-selected', label: 'Update selected', action: 'update-selected', requiresSelection: true },
  { id: 'mass-delete', label: 'Mass delete', dialog: 'mass-delete', requiresSelection: true },
  { id: 'save-definitions', label: 'Save', dialog: 'save-definitions', requiresSelection: true },
  { id: 'load-definitions', label: 'Load', dialog: 'load-definitions' },
] as const;
