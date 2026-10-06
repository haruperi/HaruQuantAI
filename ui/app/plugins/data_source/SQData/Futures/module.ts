import type { DataSourceProvider } from '../../Common/dataSourceRibbon';
import { futuresAddCommand } from './add/module';
import { futuresUpdateCommand } from './update/module';
export { SQFuturesAddPopup } from './add/module';
export { runFuturesUpdate } from './update/module';
export const futuresProvider: DataSourceProvider = { id: 'sq-futures', label: 'Futures data', commands: [futuresAddCommand, futuresUpdateCommand] };
