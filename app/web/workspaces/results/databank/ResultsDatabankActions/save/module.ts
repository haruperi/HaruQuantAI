import { label as sourceCode } from './sourceCode/module';
import { label as sq4 } from './saveToSQ4/module';
import { label as html } from './exportHTML/module';
import { label as pdf } from './exportPDF/module';
import { label as csv } from './exportCSV/module';
import { label as sq3 } from './saveToSQ3/module';
import { label as trades } from './exportStrategyTrades/module';

/** Preserve the seven existing flat Save choices from bounded descriptors. */
export const SAVE_MENU = [sq4, html, pdf, sourceCode, csv, sq3, trades];
export { SaveRecordsDialog } from './savePopup';
export { openSimulatedSave, completeSimulatedSave } from './SaveButtonService';
