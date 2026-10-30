import { create } from 'zustand';
import {
  DEFAULT_VIEW_PRESETS,
  type DatabankView,
  type DatabankViewColumn,
} from './databankColumns';

// v2: default preset renamed to the donor view name and reordered (UI-BUILDER-DATABANK-003);
// bumping the key discards stale v1 presets that lack the new default view.
const STORAGE_KEY_VIEWS = 'sqx-databank-views-v2';
const STORAGE_KEY_ACTIVE = 'sqx-databank-active-view-id-v2';

function safeGetItem(key: string): string | null {
  try {
    if (typeof localStorage !== 'undefined') {
      return localStorage.getItem(key);
    }
  } catch {
    // Ignore
  }
  return null;
}

function safeSetItem(key: string, value: string): void {
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(key, value);
    }
  } catch {
    // Ignore
  }
}

function safeRemoveItem(key: string): void {
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem(key);
    }
  } catch {
    // Ignore
  }
}

function loadInitialViews(): DatabankView[] {
  try {
    const raw = safeGetItem(STORAGE_KEY_VIEWS);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    }
  } catch {
    // Fall back to defaults on parse/storage error
  }
  return DEFAULT_VIEW_PRESETS;
}

function loadInitialActiveId(): string {
  try {
    const raw = safeGetItem(STORAGE_KEY_ACTIVE);
    if (raw) return raw;
  } catch {
    // Fall back
  }
  return DEFAULT_VIEW_PRESETS[0]?.id || 'default-main';
}

export interface DatabankStoreState {
  views: DatabankView[];
  activeViewId: string;
  setActiveView: (id: string) => void;
  addView: (view: DatabankView) => void;
  updateView: (view: DatabankView) => void;
  deleteView: (id: string) => void;
  cloneView: (sourceId: string, newName: string) => DatabankView;
  resetViews: () => void;
  setColumnWidth: (viewId: string, columnId: string, width: number) => void;
  getActiveView: () => DatabankView;
}

export const useDatabankStore = create<DatabankStoreState>((set, get) => ({
  views: loadInitialViews(),
  activeViewId: loadInitialActiveId(),

  setActiveView: (id: string) => {
    set({ activeViewId: id });
    safeSetItem(STORAGE_KEY_ACTIVE, id);
  },

  addView: (view: DatabankView) => {
    set(state => {
      const updated = [...state.views, view];
      safeSetItem(STORAGE_KEY_VIEWS, JSON.stringify(updated));
      return { views: updated, activeViewId: view.id };
    });
  },

  updateView: (view: DatabankView) => {
    set(state => {
      const updated = state.views.map(v => (v.id === view.id ? view : v));
      safeSetItem(STORAGE_KEY_VIEWS, JSON.stringify(updated));
      return { views: updated };
    });
  },

  deleteView: (id: string) => {
    set(state => {
      const viewToDelete = state.views.find(v => v.id === id);
      if (viewToDelete?.isDefault) {
        return state; // Cannot delete default preset
      }
      const updated = state.views.filter(v => v.id !== id);
      const nextActive =
        state.activeViewId === id
          ? updated[0]?.id || 'default-main'
          : state.activeViewId;
      safeSetItem(STORAGE_KEY_VIEWS, JSON.stringify(updated));
      safeSetItem(STORAGE_KEY_ACTIVE, nextActive);
      return { views: updated, activeViewId: nextActive };
    });
  },

  cloneView: (sourceId: string, newName: string) => {
    const source = get().views.find(v => v.id === sourceId) || get().views[0];
    const newId = `custom-view-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`;
    const cloned: DatabankView = {
      id: newId,
      name: newName.trim() || `${source.name} (Copy)`,
      isDefault: false,
      columns: source.columns.map((c: DatabankViewColumn) => ({ ...c })),
    };
    get().addView(cloned);
    return cloned;
  },

  resetViews: () => {
    set({
      views: DEFAULT_VIEW_PRESETS,
      activeViewId: DEFAULT_VIEW_PRESETS[0].id,
    });
    safeRemoveItem(STORAGE_KEY_VIEWS);
    safeSetItem(STORAGE_KEY_ACTIVE, DEFAULT_VIEW_PRESETS[0].id);
  },

  setColumnWidth: (viewId: string, columnId: string, width: number) => {
    set(state => {
      const updated = state.views.map(v => {
        if (v.id !== viewId) return v;
        const colExists = v.columns.some(c => c.columnId === columnId);
        const newCols = colExists
          ? v.columns.map(c => (c.columnId === columnId ? { ...c, width } : c))
          : [...v.columns, { columnId, width }];
        return { ...v, columns: newCols };
      });
      safeSetItem(STORAGE_KEY_VIEWS, JSON.stringify(updated));
      return { views: updated };
    });
  },

  getActiveView: () => {
    const { views, activeViewId } = get();
    return views.find(v => v.id === activeViewId) || views[0] || DEFAULT_VIEW_PRESETS[0];
  },
}));
