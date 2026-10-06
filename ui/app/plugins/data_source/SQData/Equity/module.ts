import type { DataSourceProvider } from '../../Common/dataSourceRibbon';
import { equityAddCommand } from './add/module';
import { equityUpdateCommand } from './update/module';
export { SQEquityAddPopup } from './add/module';
export { runEquityUpdate } from './update/module';
export const equityProvider: DataSourceProvider = { id: 'sq-equity', label: 'Equity data', commands: [equityAddCommand, equityUpdateCommand] };
