/**
 * Selection Presentation Context for HaruQuantAI D-UI.
 *
 * Implements multi-widget synchronized selection contexts based on ClientSelection (record R8).
 */

import React, { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import type { ClientSelection } from "../contracts/generated/ui";

export interface SelectionContextValue {
  getSelection: (selectionId: string) => ClientSelection;
  setSelection: (selection: ClientSelection) => void;
  selectKeys: (selectionId: string, keys: string[], replace?: boolean) => void;
  toggleKey: (selectionId: string, key: string) => void;
  selectAll: (selectionId: string, isAllSelected: boolean) => void;
  clearSelection: (selectionId: string) => void;
}

const SelectionContext = createContext<SelectionContextValue | null>(null);

export const SelectionProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [selections, setSelections] = useState<Map<string, ClientSelection>>(new Map());

  const getSelection = useCallback(
    (selectionId: string): ClientSelection => {
      return (
        selections.get(selectionId) || {
          selection_id: selectionId,
          selected_keys: [],
          is_all_selected: false,
          schema_version: 1,
        }
      );
    },
    [selections]
  );

  const setSelection = useCallback((selection: ClientSelection) => {
    setSelections((prev) => {
      const next = new Map(prev);
      next.set(selection.selection_id, selection);
      return next;
    });
  }, []);

  const selectKeys = useCallback(
    (selectionId: string, keys: string[], replace: boolean = true) => {
      setSelections((prev) => {
        const next = new Map(prev);
        const current = prev.get(selectionId) || {
          selection_id: selectionId,
          selected_keys: [],
          is_all_selected: false,
          schema_version: 1,
        };

        const updatedKeys = replace
          ? [...keys]
          : Array.from(new Set([...(current.selected_keys || []), ...keys]));

        next.set(selectionId, {
          ...current,
          selected_keys: updatedKeys,
          is_all_selected: false,
        });
        return next;
      });
    },
    []
  );

  const toggleKey = useCallback((selectionId: string, key: string) => {
    setSelections((prev) => {
      const next = new Map(prev);
      const current = prev.get(selectionId) || {
        selection_id: selectionId,
        selected_keys: [],
        is_all_selected: false,
        schema_version: 1,
      };

      const keysSet = new Set(current.selected_keys || []);
      if (keysSet.has(key)) {
        keysSet.delete(key);
      } else {
        keysSet.add(key);
      }

      next.set(selectionId, {
        ...current,
        selected_keys: Array.from(keysSet),
        is_all_selected: false,
      });
      return next;
    });
  }, []);

  const selectAll = useCallback((selectionId: string, isAllSelected: boolean) => {
    setSelections((prev) => {
      const next = new Map(prev);
      const current = prev.get(selectionId) || {
        selection_id: selectionId,
        selected_keys: [],
        is_all_selected: false,
        schema_version: 1,
      };

      next.set(selectionId, {
        ...current,
        is_all_selected: isAllSelected,
      });
      return next;
    });
  }, []);

  const clearSelection = useCallback((selectionId: string) => {
    setSelections((prev) => {
      const next = new Map(prev);
      next.set(selectionId, {
        selection_id: selectionId,
        selected_keys: [],
        is_all_selected: false,
        schema_version: 1,
      });
      return next;
    });
  }, []);

  return (
    <SelectionContext.Provider
      value={{
        getSelection,
        setSelection,
        selectKeys,
        toggleKey,
        selectAll,
        clearSelection,
      }}
    >
      {children}
    </SelectionContext.Provider>
  );
};

export function useSelection(selectionId: string) {
  const ctx = useContext(SelectionContext);
  if (!ctx) {
    throw new Error("useSelection must be used within a SelectionProvider");
  }

  const selection = ctx.getSelection(selectionId);
  const selectedKeys = selection.selected_keys || [];
  const isAllSelected = selection.is_all_selected || false;

  return {
    selection,
    selectedKeys,
    isAllSelected,
    isSelected: (key: string) => isAllSelected || selectedKeys.includes(key),
    select: (keys: string[], replace: boolean = true) =>
      ctx.selectKeys(selectionId, keys, replace),
    toggle: (key: string) => ctx.toggleKey(selectionId, key),
    selectAll: (all: boolean) => ctx.selectAll(selectionId, all),
    clear: () => ctx.clearSelection(selectionId),
  };
}
