import { label as sq4 } from './saveToSQ4/module';
import { label as html } from './exportHTML/module';
import { label as pdf } from './exportPDF/module';
import { label as csv } from './exportCSV/module';
import { label as sq3 } from './saveToSQ3/module';
import { label as trades } from './exportStrategyTrades/module';

/** Source code keeps its existing flat choice until the approved Group5 integration. */
export const SAVE_MENU = [sq4, html, pdf, 'Source code', csv, sq3, trades];
export { SaveRecordsDialog } from './savePopup';
export { openSimulatedSave, completeSimulatedSave } from './SaveButtonService';
