import {useEffect,type ReactNode} from 'react';
export function SqdModal({
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
      className="modal-backdrop sqx-dialog-scope sqd-dialog-scope"
      role="presentation"
      onMouseDown={e => e.target === e.currentTarget && onClose()}
    >
      <div className="modal sqx-modal sqd-modal" role="dialog" aria-modal="true" style={{ width }}>
        <header>
          <h2>{title}</h2>
          <button type="button" className="sqx-modal-close" aria-label="Close" onClick={onClose}>
            &times;
          </button>
        </header>
        <div className="modal-content">{children}</div>
        {footer !== undefined && <footer>{footer}</footer>}
      </div>
    </div>
  );
}
