import { useEffect, useRef, useState } from 'react';
import type { Dispatch, RefObject, SetStateAction } from 'react';
import { ApiClientError } from '../../../shell/transport';
import { homeClient } from '../homeClient';
import { useProjectBinding } from '../projectController';

export type NotesSaveState = 'idle' | 'saving' | 'saved' | 'conflict' | 'error';
export interface NotesControllerOptions {
  projectId?: string | null; initialRevision?: number; initialNotes?: string;
  onRevisionChange?: (rev: number) => void; client?: ReturnType<typeof homeClient>;
}
export interface SaveNotesActionResult { saveState: NotesSaveState; revision: number; error: string | null }
export async function executeSaveNotes(projectId: string | null | undefined, content: string, revision: number, client?: ReturnType<typeof homeClient>): Promise<SaveNotesActionResult> {
  if (!projectId?.trim()) return { saveState: 'error', revision, error: 'Cannot save notes: No active project is loaded' };
  try {
    const result = await (client ?? homeClient()).saveNotes(projectId, content, revision);
    if (result.status !== 'saved' || result.notes !== content) throw new Error('Notes save was not acknowledged.');
    return { saveState: 'saved', revision: result.revision, error: null };
  } catch (error) {
    const conflict = error instanceof ApiClientError ? error.status === 409 || error.code === 'conflict' : /409|conflict/i.test(String(error));
    return { saveState: conflict ? 'conflict' : 'error', revision, error: conflict ? 'Revision conflict: notes were modified concurrently; your draft is preserved.' : String(error) };
  }
}
export interface NotesController {
  areaRef: RefObject<HTMLTextAreaElement | null>; content: string; change: (value: string) => void;
  saved: boolean; setSaved: Dispatch<SetStateAction<boolean>>; saveState: NotesSaveState;
  error: string | null; revision: number; projectId?: string; canSave: boolean;
  save: (overrideProjectId?: string) => Promise<void>;
}
export function useNotesController(options: NotesControllerOptions = {}): NotesController {
  const binding = useProjectBinding();
  const projectId = options.projectId ?? binding?.state.project?.manifest.project_id;
  const initialNotes = options.initialNotes ?? binding?.state.project?.metadata?.notes;
  const currentRevision = options.initialRevision ?? binding?.state.project?.revision;
  const [content, setContent] = useState(typeof initialNotes === 'string' ? initialNotes : '');
  const [revision, setRevision] = useState(currentRevision ?? 0), [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false), [saveState, setSaveState] = useState<NotesSaveState>('idle');
  const [error, setError] = useState<string | null>(null);
  const areaRef = useRef<HTMLTextAreaElement | null>(null), generation = useRef(0), saving = useRef(false);
  const drafts = useRef(new Map<string, string>());
  useEffect(() => {
    const token = ++generation.current, abort = new AbortController();
    setSaveState('idle'); setError(null); setSaved(false); setRevision(currentRevision ?? 0);
    setContent(projectId ? drafts.current.get(projectId) ?? (typeof initialNotes === 'string' ? initialNotes : '') : '');
    if (!projectId || currentRevision !== undefined) return () => { generation.current++; };
    setLoading(true);
    void (options.client ?? homeClient({ signal: abort.signal })).getProject(projectId).then(project => {
      if (token !== generation.current) return;
      setRevision(project.revision); setContent(drafts.current.get(projectId) ?? project.metadata?.notes ?? ''); setLoading(false);
    }).catch(failure => { if (token === generation.current) { setError(String(failure)); setLoading(false); } });
    return () => { abort.abort(); generation.current++; };
  }, [projectId]);
  useEffect(() => { if (currentRevision !== undefined) setRevision(currentRevision); }, [currentRevision]);
  const change = (value: string) => { if (projectId) drafts.current.set(projectId, value); setContent(value); setSaved(false); setSaveState('idle'); };
  const save = async () => {
    if (saving.current || !projectId || loading) return;
    saving.current = true;
    const token = generation.current, sent = content;
    setSaveState('saving'); setError(null);
    const result = await executeSaveNotes(projectId, sent, revision, options.client);
    saving.current = false;
    if (token !== generation.current) return;
    setSaveState(result.saveState); setRevision(result.revision); setError(result.error);
    if (result.saveState === 'saved') {
      const unchanged = (drafts.current.get(projectId) ?? sent) === sent;
      setSaved(unchanged); if (!unchanged) setSaveState('idle');
      if (unchanged) drafts.current.delete(projectId);
      binding?.controller.noteRevision(result.revision, sent); options.onRevisionChange?.(result.revision);
    }
  };
  return { areaRef, content, change, saved, setSaved, saveState, error, revision, projectId: projectId ?? undefined,
    canSave: !!projectId && revision > 0 && !loading, save };
}
