import type { ButtonHTMLAttributes, ReactNode } from 'react';
export function ToolButton({
  label,
  shortcut,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string;
  shortcut?: string;
  children: ReactNode;
}) {
  return (
    <span className="cq-tooltip-wrap">
      <button type="button" aria-label={label} {...props}>
        {children}
      </button>
      <span role="tooltip">
        {label}
        {shortcut && <kbd>{shortcut}</kbd>}
      </span>
    </span>
  );
}
