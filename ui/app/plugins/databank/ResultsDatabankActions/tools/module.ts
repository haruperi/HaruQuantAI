import { SELECT_MENU } from './select/module';
import { SET_NOTE_MENU } from './setNote/module';

/** Preserve childless leaves and their currently inactive toolbar presentation. */
export const TOOLS_MENU = [
  { label: 'Edit', children: ['Parameters', 'Strategy'] },
  SELECT_MENU,
  SET_NOTE_MENU,
  { label: 'Compare' },
  { label: 'Run CA' },
];
export { handleSelectItem, strategyPassesMockChecks } from './select/module';
export { requestSetNote, applySetNote, SetNoteDialog } from './setNote/module';
