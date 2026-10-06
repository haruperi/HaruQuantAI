import { useEffect } from 'react';
import type { ReactNode } from 'react';

/**
 * SQX-style databanks dialogs (donor evidence retained target UI; current donor equivalence unverified).
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
