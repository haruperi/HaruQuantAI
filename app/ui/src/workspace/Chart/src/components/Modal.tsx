import { useEffect, useRef, type ReactNode } from 'react';
import { X } from 'lucide-react';
import { useChart } from '../hooks/useChartEngine';
import { ToolButton } from './Tooltip';
export function Modal({ title, children }: { title: string; children: ReactNode }) {
  const { store } = useChart(),
    ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous = document.activeElement;
    const modal = ref.current;
    modal?.querySelector<HTMLElement>('input,select,button')?.focus();
    return () => {
      if (previous instanceof HTMLElement) previous.focus();
    };
  }, []);
  return (
    <div
      className="cq-backdrop"
      onPointerDown={(e) => {
        if (e.target === e.currentTarget) store.getState().setUI({ dialog: null });
      }}
    >
      <div
        className="cq-modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        ref={ref}
        onKeyDown={(e) => {
          if (e.key === 'Escape') {
            e.stopPropagation();
            store.getState().setUI({ dialog: null });
          }
          if (e.key === 'Tab') {
            const controls = ref.current?.querySelectorAll<HTMLElement>(
              'button:not(:disabled),input,select,textarea,[tabindex="0"]',
            );
            if (!controls?.length) return;
            const first = controls[0],
              last = controls[controls.length - 1];
            if (e.shiftKey && document.activeElement === first) {
              e.preventDefault();
              last.focus();
            }
            if (!e.shiftKey && document.activeElement === last) {
              e.preventDefault();
              first.focus();
            }
          }
        }}
      >
        <header>
          <h2>{title}</h2>
          <ToolButton
            label="Close dialog"
            shortcut="Esc"
            onClick={() => store.getState().setUI({ dialog: null })}
          >
            <X size={19} />
          </ToolButton>
        </header>
        {children}
      </div>
    </div>
  );
}
