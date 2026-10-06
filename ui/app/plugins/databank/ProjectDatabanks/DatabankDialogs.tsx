import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';

/**
 * SQX-parity databanks dialogs (donor evidence SQX144-EV-000030).
 * Titles, fields, buttons, and message texts follow the installed donor
 * templates verbatim, including the donor misspelling in the Retest title.
 */

export function SqxModal({
  title,
  onClose,
  children,
  footer,
  width = 450,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  width?: number;
}) {
  useEffect(() => {
    const close = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', close);
    return () => document.removeEventListener('keydown', close);
  }, [onClose]);

  return (
    <div
      className="modal-backdrop sqx-dialog-scope"
      role="presentation"
      onMouseDown={e => e.target === e.currentTarget && onClose()}
    >
      <div className="modal sqx-modal" role="dialog" aria-modal="true" style={{ width }}>
        <header>
          <h2>{title}</h2>
          <button type="button" className="sqx-modal-close" aria-label="Close" onClick={onClose}>
            ×
          </button>
        </header>
        <div className="modal-content">{children}</div>
        {footer && <footer>{footer}</footer>}
      </div>
    </div>
  );
}

export function SqxButton({
  children,
  onClick,
  primary,
}: {
  children: ReactNode;
  onClick: () => void;
  primary?: boolean;
}) {
  return (
    <button type="button" className={`sqx-btn${primary ? ' primary' : ''}`} onClick={onClick}>
      {children}
    </button>
  );
}

/** Donor "Removing reports" confirm used by Delete and Clear all. */
export function RemovingReportsConfirm({
  message,
  confirmLabel = 'Yes',
  onConfirm,
  onClose,
}: {
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onClose: () => void;
}) {
  return (
    <SqxModal title="Removing reports" onClose={onClose} width={420}
      footer={
        <>
          <SqxButton onClick={onClose}>No</SqxButton>
          <SqxButton primary onClick={() => { onConfirm(); onClose(); }}>{confirmLabel}</SqxButton>
        </>
      }
    >
      <p className="sqx-dialog-text">{message}</p>
    </SqxModal>
  );
}

/** Donor Load popup: "Loading records" with a striped progress bar. */
export function LoadRecordsDialog({ onFinished }: { onFinished: () => void }) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress(p => {
        if (p >= 100) {
          clearInterval(timer);
          return 100;
        }
        return Math.min(100, p + 10);
      });
    }, 120);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (progress >= 100) {
      const t = setTimeout(onFinished, 350);
      return () => clearTimeout(t);
    }
  }, [progress, onFinished]);

  return (
    <SqxModal title="Loading records" onClose={onFinished}>
      <p className="sqx-dialog-text">Loading selected records into databank...</p>
      <div className="sqx-progress" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
        <div className="sqx-progress-bar" style={{ width: `${progress}%` }}>{progress}%</div>
      </div>
    </SqxModal>
  );
}

/**
 * Donor Retest confirm. The title keeps the donor misspelling ("seleted")
 * verbatim for parity; flagged in the task walkthrough.
 */
export function RetestDialog({
  onMove,
  onClose,
}: {
  onMove: (removeFromDatabank: boolean) => void;
  onClose: () => void;
}) {
  const [applyConfig, setApplyConfig] = useState(false);
  return (
    <SqxModal title="Do you want to copy seleted strategies to Retester?" onClose={onClose} width={450}
      footer={
        <>
          <SqxButton onClick={onClose}>Cancel</SqxButton>
          <SqxButton primary onClick={() => { onMove(false); onClose(); }}>Copy (keep original)</SqxButton>
          <SqxButton primary onClick={() => { onMove(true); onClose(); }}>Move (remove from this databank)</SqxButton>
        </>
      }
    >
      <label className="sqx-check">
        <input
          type="checkbox"
          checked={applyConfig}
          onChange={e => setApplyConfig(e.target.checked)}
        />
        <span>
          Apply current config
          <br />
          This will overwrite your Retester config with this task's one.
        </span>
      </label>
    </SqxModal>
  );
}

/** Donor Save popup structure: directory browse, prefix/suffix, format radios. */
export function SaveRecordsDialog({
  format,
  onSave,
  onClose,
}: {
  format: string;
  onSave: () => void;
  onClose: () => void;
}) {
  const [prefix, setPrefix] = useState('Strategy');
  const [suffix, setSuffix] = useState('');
  return (
    <SqxModal title={`Save / ${format}`} onClose={onClose}
      footer={
        <>
          <SqxButton onClick={onClose}>Cancel</SqxButton>
          <SqxButton primary onClick={() => { onSave(); onClose(); }}>Save</SqxButton>
        </>
      }
    >
      <div className="sqx-form-row">
        <label>Directory</label>
        <input className="sqx-input" value="C:\\Users\\demo\\Documents\\StrategyQuant X" readOnly />
        <SqxButton onClick={onClose}>Browse</SqxButton>
      </div>
      <div className="sqx-form-row">
        <label>File name</label>
        <input className="sqx-input" value={prefix} onChange={e => setPrefix(e.target.value)} />
        <span className="sqx-form-hint">Strategy X.y.z</span>
        <input className="sqx-input" value={suffix} onChange={e => setSuffix(e.target.value)} />
      </div>
      <p className="sqx-help">
        Selected strategies will be saved to a directory of your choice with given prefix and sufix.
        If file with the same name already exists, it will be overwritten!
      </p>
    </SqxModal>
  );
}

/** Tools > Set note dialog (one-field, rename-style). */
export function SetNoteDialog({
  currentNote,
  onSetNote,
  onClose,
}: {
  currentNote: string;
  onSetNote: (note: string) => void;
  onClose: () => void;
}) {
  const [note, setNote] = useState(currentNote);
  return (
    <SqxModal title="Set note" onClose={onClose}
      footer={
        <>
          <SqxButton onClick={onClose}>Cancel</SqxButton>
          <SqxButton primary onClick={() => { onSetNote(note); onClose(); }}>Set note</SqxButton>
        </>
      }
    >
      <textarea
        className="sqx-input sqx-textarea"
        value={note}
        onChange={e => setNote(e.target.value)}
        rows={4}
        autoFocus
      />
    </SqxModal>
  );
}
