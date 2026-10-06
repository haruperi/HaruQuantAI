import { PORTFOLIO_MENU } from '../ResultsDatabankActions/portfolio/module';
import { SAVE_MENU } from '../ResultsDatabankActions/save/module';
import { TOOLS_MENU } from '../ResultsDatabankActions/tools/module';
export { TOOLS_MENU } from '../ResultsDatabankActions/tools/module';
import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';

/**
 * SQX-style databanks toolbar (donor evidence retained target UI; current donor equivalence unverified).
 * Button order and menu trees come from the installed action plugins:
 * Load(10) Save:(20) Delete(30) Clear all(40) Retest(50) Rename(55)
 * Filter by correlation(56) Portfolio:(60) Tools:(70), icon refresh(190),
 * right-aligned View combo and Manage Views gear.
 */

export type ToolbarAction =
  | 'load'
  | 'save'
  | 'delete'
  | 'clearAll'
  | 'retest'
  | 'rename'
  | 'filterByCorrelation'
  | 'portfolio'
  | 'tools'
  | 'refresh'
  | 'manageViews';

export const TOOLBAR_BUTTON_ORDER: { id: ToolbarAction; label: string; destructive?: boolean }[] = [
  { id: 'load', label: 'Load' },
  { id: 'save', label: 'Save' },
  { id: 'delete', label: 'Delete', destructive: true },
  { id: 'clearAll', label: 'Clear all', destructive: true },
  { id: 'retest', label: 'Retest' },
  { id: 'rename', label: 'Rename' },
  { id: 'filterByCorrelation', label: 'Filter by correlation' },
  { id: 'portfolio', label: 'Portfolio' },
  { id: 'tools', label: 'Tools' },
];

export { SAVE_MENU } from '../ResultsDatabankActions/save/module';

export { PORTFOLIO_MENU } from '../ResultsDatabankActions/portfolio/module';

export interface ToolsMenuItem {
  label: string;
  children?: string[];
}

function useOutsideClose(onClose: () => void) {
  const ref = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onClose]);
  return ref;
}

function ToolbarDropdown({
  label,
  menuId,
  items,
  submenus,
  onItem,
}: {
  label: string;
  menuId: string;
  items?: string[];
  submenus?: ToolsMenuItem[];
  onItem: (item: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useOutsideClose(() => setOpen(false));

  const pick = (item: string) => {
    setOpen(false);
    onItem(item);
  };

  return (
    <div className="sqx-tb-dropdown" ref={ref}>
      <button
        type="button"
        className={`sqx-btn${open ? ' open' : ''}`}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen(o => !o)}
      >
        {label}
        <span className="sqx-caret" aria-hidden="true" />
      </button>
      {open && (
        <div className="sqx-menu" role="menu" aria-label={`${label} menu`}>
          {items?.map(item => (
            <button type="button" role="menuitem" key={item} onClick={() => pick(item)}>
              {item}
            </button>
          ))}
          {submenus?.map(group => (
            <div className="sqx-menu-group" key={group.label} data-menu-id={`tools-${group.label.toLowerCase()}`}>
              <button type="button" role="menuitem" aria-haspopup="menu" className="sqx-submenu-trigger">
                {group.label}
                <span className="sqx-caret right" aria-hidden="true" />
              </button>
              <div className="sqx-submenu" role="menu">
                {group.children?.map(child => (
                  <button type="button" role="menuitem" key={child} data-menu-id={`${menuId}-${group.label}-${child}`.toLowerCase()} onClick={() => pick(`${group.label}:${child}`)}>
                    {child}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function DatabankToolbar({
  records,
  selectedCount,
  viewNames,
  activeView,
  onViewChange,
  onAction,
}: {
  records: number;
  selectedCount: number;
  viewNames: string[];
  activeView: string;
  onViewChange: (name: string) => void;
  onAction: (action: ToolbarAction, menuItem?: string) => void;
}) {
  return (
    <div className="sqx-toolbar">
      <div className="sqx-toolbar-left">
        {TOOLBAR_BUTTON_ORDER.map(({ id, label, destructive }) => {
          if (id === 'save') {
            return (
              <ToolbarDropdown
                key={id}
                label={label}
                menuId="save"
                items={SAVE_MENU}
                onItem={item => onAction('save', item)}
              />
            );
          }
          if (id === 'portfolio') {
            return (
              <ToolbarDropdown
                key={id}
                label={label}
                menuId="portfolio"
                items={PORTFOLIO_MENU}
                onItem={item => onAction('portfolio', item)}
              />
            );
          }
          if (id === 'tools') {
            return (
              <ToolbarDropdown
                key={id}
                label={label}
                menuId="tools"
                submenus={TOOLS_MENU}
                onItem={item => onAction('tools', item)}
              />
            );
          }
          return (
            <button
              type="button"
              key={id}
              className={`sqx-btn${destructive ? ' destructive' : ''}`}
              onClick={() => onAction(id)}
            >
              {label}
            </button>
          );
        })}
      </div>

      <div className="sqx-records-count" title="Records in the active databank">
        Records: {records}
        {selectedCount > 0 && <> (Selected: {selectedCount})</>}
      </div>

      <div className="sqx-toolbar-right">
        <button
          type="button"
          className="sqx-btn sqx-icon-btn"
          title="Refresh databank content"
          aria-label="Refresh databank content"
          onClick={() => onAction('refresh')}
        >
          <svg width="13" height="13" viewBox="0 0 16 16" aria-hidden="true">
            <path
              d="M13.6 2.4v3.9H9.7l1.4-1.4a4.4 4.4 0 1 0 1 4.3l1.6.5a6 6 0 1 1-1.4-6L13.6 2.4z"
              fill="#4a5460"
            />
          </svg>
        </button>
        <label className="sqx-view-combo">
          View:
          <select value={activeView} onChange={e => onViewChange(e.target.value)} aria-label="Databank view">
            {viewNames.map(v => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          className="sqx-btn sqx-icon-btn"
          title="Settings"
          aria-label="Manage databank views"
          onClick={() => onAction('manageViews')}
        >
          <svg width="13" height="13" viewBox="0 0 16 16" aria-hidden="true">
            <path
              d="M1.6 9.7a6.5 6.5 0 0 1 0-3.4l1.7-.2.7-1.6-.9-1.4a6.5 6.5 0 0 1 3-1.7l1 1.2h1.8l1-1.2a6.5 6.5 0 0 1 3 1.7l-.9 1.4.7 1.6 1.7.2a6.5 6.5 0 0 1 0 3.4l-1.7.2-.7 1.6.9 1.4a6.5 6.5 0 0 1-3 1.7l-1-1.2H5.1l-1 1.2a6.5 6.5 0 0 1-3-1.7l.9-1.4-.7-1.6-1.7-.2zM6.4 10a2.3 2.3 0 1 0 3.2-3.3A2.3 2.3 0 0 0 6.4 10z"
              fill="#4a5460"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}
