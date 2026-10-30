import type { DataSourceProvider } from '../Common/dataSourceRibbon';
import { tdImportCommand } from './import/module';
export { TickDownloaderImportDialog } from './import/module';
export const tdProvider: DataSourceProvider = { id: 'tickdownloader', label: 'TickDownloader import', commands: [tdImportCommand] };
