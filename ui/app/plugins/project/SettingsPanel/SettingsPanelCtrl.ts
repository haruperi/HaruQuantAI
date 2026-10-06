import { useState } from 'react';
import type { SettingsSection } from '../ProjectWorkbench/contracts';

/** Existing controlled or local settings selection, without task discovery. */
export function useSettingsPanel(sections: SettingsSection[], selectedId?: string, onSelect?: (id: string) => void) {
  const [localId, setLocalId] = useState(sections[0]?.id);
  const activeId = selectedId ?? localId;
  const setActiveId = (id: string) => { setLocalId(id); onSelect?.(id); };
  const active = sections.find(section => section.id === activeId) ?? sections[0];
  return { active, setActiveId };
}
