import { useNotesController, type NotesControllerOptions } from './NotesCtrl';

export interface NotesTabProps extends NotesControllerOptions {
  className?: string;
}

/**
 * "Notes" tab: Save button with live persistence status, plain-text Unicode editor.
 */
export function NotesTab({
  projectId,
  initialRevision,
  initialNotes,
  onRevisionChange,
  client,
  className,
}: NotesTabProps = {}) {
  const { areaRef, saveState, error, save, content, change, canSave } = useNotesController({
    projectId,
    initialRevision,
    initialNotes,
    onRevisionChange,
    client,
  });

  return (
    <div className={`notesWrapper sqd-tab-content ${className ?? ''}`.trim()}>
      <div className="notesToolbar sqd-notes-toolbar">
        <button
          type="button"
          className="sqd-btn sqd-btn-primary"
          disabled={!canSave || saveState === 'saving'}
          title={!canSave ? 'Cannot save notes: No active project is loaded' : 'Save notes'}
          aria-label={!canSave ? 'Save notes (disabled - no active project)' : 'Save notes'}
          onClick={() => void save()}
        >
          {saveState === 'saving' ? 'Saving...' : 'Save'}
        </button>
        {saveState === 'saved' && <span className="sqd-notes-saved">Saved</span>}
        {saveState === 'conflict' && (
          <span className="sqd-notes-conflict text-danger" role="alert">
            {error ?? 'Conflict: notes modified concurrently'}
          </span>
        )}
        {saveState === 'error' && (
          <span className="sqd-notes-error text-danger" role="alert">
            {error ?? 'Error saving notes'}
          </span>
        )}
      </div>
      <textarea
        value={content}
        onChange={event => change(event.target.value)}
        readOnly={!canSave || saveState === 'saving'}
        className="notesContainer sqd-notes-container"
        ref={areaRef}
        role="textbox"
        aria-multiline="true"
        aria-label="Notes"
      />
    </div>
  );
}
