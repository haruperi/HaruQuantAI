import { type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode, useEffect } from 'react';
import { X } from 'lucide-react';

export function Button({ className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement>) { return <button className={`sq-button ${className}`} {...props} />; }
export function IconButton({ title, children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { title: string; children: ReactNode }) { return <button className="icon-button" title={title} aria-label={title} {...props}>{children}</button>; }
export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) { return <label className="field"><span>{label}</span>{children}{hint && <small>{hint}</small>}</label>; }
export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) { return <input className="text-input" {...props} />; }
export function Checkbox({ label, checked, onChange, disabled }: { label: string; checked: boolean; onChange: (value: boolean) => void; disabled?: boolean }) { return <label className={`check ${disabled ? 'disabled' : ''}`}><input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} disabled={disabled}/><span>{label}</span></label>; }
export function Select({ value, onChange, children, disabled }: { value: string; onChange: (value: string) => void; children: ReactNode; disabled?: boolean }) { return <select className="text-input" value={value} onChange={e => onChange(e.target.value)} disabled={disabled}>{children}</select>; }
export function Section({ title, description, children, actions }: { title: string; description?: string; children: ReactNode; actions?: ReactNode }) { return <section className="section"><header><div><h3>{title}</h3>{description && <p>{description}</p>}</div>{actions}</header><div className="section-body">{children}</div></section>; }
export function Modal({ title, onClose, children, footer, width = 620 }: { title: string; onClose: () => void; children: ReactNode; footer?: ReactNode; width?: number }) {
  useEffect(() => { const close = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); }; document.addEventListener('keydown', close); return () => document.removeEventListener('keydown', close); }, [onClose]);
  return <div className="modal-backdrop" role="presentation" onMouseDown={e => e.target === e.currentTarget && onClose()}><div className="modal" role="dialog" aria-modal="true" style={{ width }}><header><h2>{title}</h2><IconButton title="Close" onClick={onClose}><X size={16}/></IconButton></header><div className="modal-content">{children}</div>{footer && <footer>{footer}</footer>}</div></div>;
}
export function ProgressBar({ value, label }: { value: number; label?: string }) { return <div className="progress-track"><div style={{ width: `${Math.max(0, Math.min(100, value))}%` }}><span>{label ?? `${Math.round(value)}%`}</span></div></div>; }
export function Stat({ label, value, tone }: { label: string; value: ReactNode; tone?: 'good' | 'bad' }) { return <div className="stat"><span>{label}</span><strong className={tone}>{value}</strong></div>; }
