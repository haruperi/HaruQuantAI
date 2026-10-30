import type { DataSourceCommand } from '../../Common/dataSourceRibbon';
export { DownloadPopup } from './downloadPopup';
export const downloadCommand = { id: 'darwinex-download', label: 'Download data for existing symbols', icon: 'download', dialog: 'darwinex-download' } as const satisfies DataSourceCommand;
