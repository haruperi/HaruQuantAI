import { useEffect, useId, useRef, type ReactNode } from "react";
import { X } from "lucide-react";
export function AWModal({
  title,
  children,
  footer,
  onClose,
  wide = false,
}: {
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const id = useId();
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const root = ref.current;
    (
      root?.querySelector<HTMLElement>("input,select,textarea") ??
      root?.querySelector<HTMLElement>("button")
    )?.focus();
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        closeRef.current();
      }
      if (e.key === "Tab" && root) {
        const items = Array.from(
          root.querySelectorAll<HTMLElement>(
            "button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href]",
          ),
        ).filter((x) => x.offsetParent !== null);
        if (!items.length) return;
        const first = items[0];
        const last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    root?.addEventListener("keydown", key);
    return () => {
      root?.removeEventListener("keydown", key);
      previous?.focus();
    };
  }, []);
  return (
    <div className="aw-overlay">
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-labelledby={id}
        className={`aw-dialog ${title === "New strategy" ? "aw-new-strategy" : ""} ${wide ? "aw-wide" : ""}`}
      >
        <header>
          <span id={id}>{title}</span>
          <button aria-label={`Close ${title}`} onClick={onClose}>
            <X size={18} />
          </button>
        </header>
        <div className="aw-dialog-body">{children}</div>
        <footer>
          {footer ?? (
            <button className="aw-primary" onClick={onClose}>
              Close
            </button>
          )}
        </footer>
      </div>
    </div>
  );
}
export function AWField({
  label,
  value,
  onChange,
  options,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options?: string[];
  type?: string;
}) {
  return (
    <label className="aw-field">
      <span>{label}</span>
      {options ? (
        <select
          aria-label={label}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        >
          {options.map((o) => (
            <option key={o}>{o}</option>
          ))}
        </select>
      ) : (
        <input
          aria-label={label}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </label>
  );
}
export function AWConfirm({
  title,
  message,
  onClose,
  onConfirm,
  action = "Delete",
}: {
  title: string;
  message: string;
  onClose: () => void;
  onConfirm: () => void;
  action?: string;
}) {
  return (
    <AWModal
      title={title}
      onClose={onClose}
      footer={
        <>
          <button onClick={onClose}>Cancel</button>
          <button className="aw-primary" onClick={onConfirm}>
            {action}
          </button>
        </>
      }
    >
      <p>{message}</p>
    </AWModal>
  );
}
