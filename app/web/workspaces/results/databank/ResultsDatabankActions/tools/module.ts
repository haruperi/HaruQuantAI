import { COMPARE_MENU } from './compareStrategies/module';
import { EDIT_MENU } from './edit/module';
import { RUN_CA_MENU } from './runCa/module';
import { SELECT_MENU } from './select/module';
import { SET_NOTE_MENU } from './setNote/module';

/** Preserve childless leaves and their currently inactive toolbar presentation. */
export const TOOLS_MENU = [
  EDIT_MENU,
  SELECT_MENU,
  SET_NOTE_MENU,
  COMPARE_MENU,
  RUN_CA_MENU,
];
export { handleSelectItem, strategyPassesMockChecks } from './select/module';
export { requestSetNote, applySetNote, SetNoteDialog } from './setNote/module';
