import { useEffect, useRef, useState } from "react";
import {
  FilePlus,
  FolderOpen,
  Files,
  Undo2,
  Redo2,
  Code,
  Zap,
  Sparkles,
  Save,
  ChevronRight,
} from "lucide-react";
import type { Draft } from "./algoWizardModel";
export function AlgoWizardToolbar({
  active,
  canUndo,
  canRedo,
  saveChanges,
  recent,
  onAction,
  onRecent,
}: {
  active: boolean;
  canUndo: boolean;
  canRedo: boolean;
  saveChanges: boolean;
  recent: Draft[];
  onAction: (action: string) => void;
  onRecent: (draft: Draft) => void;
}) {
  const [open, setOpen] = useState(false);
  const [sub, setSub] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const close = (e: PointerEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    const escape = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", close);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("pointerdown", close);
      document.removeEventListener("keydown", escape);
    };
  }, []);
  const action = (name: string) => {
    setOpen(false);
    onAction(name);
  };
  return (
    <nav className="aw-topbar" aria-label="AlgoWizard toolbar">
      <strong>EDITOR</strong>
      <button onClick={() => action("new")}>
        <FilePlus size={15} />
        New
      </button>
      <div className="aw-menu-anchor" ref={ref}>
        <button
          aria-expanded={open}
          aria-haspopup="menu"
          onClick={() => {
            setOpen(!open);
            setSub(false);
          }}
        >
          <FolderOpen size={16} />
          Files
        </button>
        {open && (
          <div
            className="aw-dropdown aw-files-menu"
            role="menu"
            aria-label="Files"
          >
            <button role="menuitem" onClick={() => action("load")}>
              <FolderOpen />
              Load from file...
            </button>
            <button
              role="menuitem"
              disabled={!active}
              onClick={() => action("save")}
            >
              <Save />
              Save to file...
            </button>
            <button
              role="menuitem"
              disabled={!active}
              onClick={() => action("save-as")}
            >
              <Save />
              Save to file as...
            </button>
            <div className="aw-menu-anchor">
              <button
                role="menuitem"
                aria-expanded={sub}
                onClick={() => setSub(!sub)}
              >
                <FolderOpen />
                Open recent...
                <ChevronRight />
              </button>
              {sub && (
                <div
                  className="aw-dropdown aw-recent-menu"
                  role="menu"
                  aria-label="Recent files"
                >
                  {recent.length ? (
                    recent.map((d, i) => (
                      <button
                        role="menuitem"
                        key={i}
                        onClick={() => {
                          setOpen(false);
                          onRecent(d);
                        }}
                      >
                        {d.name}
                      </button>
                    ))
                  ) : (
                    <span>No recent files</span>
                  )}
                </div>
              )}
            </div>
            <hr />
            <button
              role="menuitem"
              disabled={!saveChanges}
              onClick={() => action("save-changes")}
            >
              <Save />
              Save changes
            </button>
            <button
              role="menuitem"
              disabled={!active}
              onClick={() => action("retester")}
            >
              <Save />
              Save to Retester
            </button>
          </div>
        )}
      </div>
      <button onClick={() => action("examples")}>
        <Files size={15} />
        Examples
      </button>
      <span className="aw-toolbar-divider" />
      <button
        title="Undo (Ctrl+Z)"
        aria-label="Undo"
        disabled={!canUndo}
        onClick={() => action("undo")}
      >
        <Undo2 size={17} />
      </button>
      <button
        title="Redo (Ctrl+Y)"
        aria-label="Redo"
        disabled={!canRedo}
        onClick={() => action("redo")}
      >
        <Redo2 size={17} />
      </button>
      <span className="aw-toolbar-divider" />
      <button disabled={!active} onClick={() => action("source")}>
        <Code size={16} />
        Source code
      </button>
      <span className="aw-toolbar-divider" />
      <button disabled={!active} onClick={() => action("results")}>
        <Zap size={16} />
        Backtest results
      </button>
      <span className="aw-toolbar-divider" />
      <button className="aw-ai-button" onClick={() => action("ai")}>
        <Sparkles size={16} />
        AI Wizard
      </button>
    </nav>
  );
}
