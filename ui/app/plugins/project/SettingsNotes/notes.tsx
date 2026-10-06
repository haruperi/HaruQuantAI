import { TOOLS, useNotesController } from './NotesCtrl';

/**
 * "Notes" tab (donor evidence SQX144-EV-000043): Save button, rich-text
 * toolbar (bold, italic, underline, align left/center/right, indent
 * more/less, horizontal rule, ordered/unordered list, link) and a
 * contenteditable area. Basic browser formatting only — no editor engine.
 */
export function NotesTab() {
  const { areaRef, saved, setSaved, exec, addLink } = useNotesController();

  return (
    <div className="notesWrapper sqd-tab-content">
      <div className="notesToolbar sqd-notes-toolbar">
        <button type="button" className="sqd-btn sqd-btn-primary" onClick={() => setSaved(true)}>Save</button>
        {saved && <span className="sqd-notes-saved">Saved (demo)</span>}
        {TOOLS.map(tool => (
          <button key={tool.cmd} type="button" className="sqd-notes-tool" title={tool.title} aria-label={tool.title} onClick={() => exec(tool.cmd)}>
            {tool.label}
          </button>
        ))}
        <button type="button" className="sqd-notes-tool" title="Link" aria-label="Link" onClick={addLink}>
          🔗
        </button>
      </div>
      <div
        className="notesContainer sqd-notes-container"
        ref={areaRef}
        contentEditable
        suppressContentEditableWarning
        role="textbox"
        aria-multiline="true"
        aria-label="Notes"
      />
    </div>
  );
}
