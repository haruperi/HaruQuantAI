import { useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { crossChecksTabDefaults, type CrossCheckTabItem } from '../ProjectWorkbench/settings/sharedSettingsFixtures';

export type CrossCheckDialog = { item: CrossCheckTabItem; kind: 'settings' | 'filters' };

/** Existing session-only snapshot and local cross-check draft. */
export interface CrossChecksController {
  checks: CrossCheckTabItem[];
  setChecks: Dispatch<SetStateAction<CrossCheckTabItem[]>>;
  notice: string;
  disabledAll: boolean;
  setDisabledAll: Dispatch<SetStateAction<boolean>>;
  dialog: CrossCheckDialog | null;
  setDialog: Dispatch<SetStateAction<CrossCheckDialog | null>>;
  toggle: (id: string) => void;
  loadSnapshot: () => void;
  saveSnapshot: () => void;
}

export function useCrossChecksController(): CrossChecksController {
  const [checks, setChecks] = useState<CrossCheckTabItem[]>(crossChecksTabDefaults);
  const [snapshot, setSnapshot] = useState<{checks:CrossCheckTabItem[];disabledAll:boolean}|null>(null);
  const [notice, setNotice] = useState('');
  const [disabledAll, setDisabledAll] = useState(false);
  const [dialog, setDialog] = useState<{ item: CrossCheckTabItem; kind: 'settings' | 'filters' } | null>(null);

  const toggle = (id: string) =>
    setChecks(current => current.map(c => (c.id === id && !disabledAll ? { ...c, use: !c.use } : c)));

  const loadSnapshot = () => { if(snapshot) {setChecks(structuredClone(snapshot.checks));setDisabledAll(snapshot.disabledAll);setNotice("Local demo snapshot restored.");} else setNotice("No local demo snapshot saved yet."); };
  const saveSnapshot = () => {setSnapshot({checks:structuredClone(checks),disabledAll});setNotice("Local demo snapshot saved for this settings session.");};
  return { checks, setChecks, notice, disabledAll, setDisabledAll, dialog, setDialog, toggle, loadSnapshot, saveSnapshot };
}
