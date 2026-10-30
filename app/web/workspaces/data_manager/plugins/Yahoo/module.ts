import type { DataSourceProvider } from '../Common/dataSourceRibbon';
import { yahooAddCommand } from './add/module';
import { yahooDownloadCommand } from './download/module';
export { YahooAddDialog } from './add/module';
export { YahooDownloadDialog } from './download/module';
export const yahooProvider: DataSourceProvider = { id: 'yahoo', label: 'Yahoo', commands: [yahooAddCommand, yahooDownloadCommand] };
