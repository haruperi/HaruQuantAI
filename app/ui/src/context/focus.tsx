/**
 * Accessibility and Focus Management Context for HaruQuantAI D-UI.
 *
 * Implements FEAT-UI-ENSURE_ACCESS foundation:
 * - Focus saving and restoration across dialogs, view replacements, and panel removals
 * - Screen-reader live region announcements (polite status and assertive error/failure notices)
 * - Keyboard navigation helpers
 */

import React, { createContext, useContext, useState, useRef, useCallback, type ReactNode } from "react";

export interface FocusManagerContextValue {
  saveFocus: (key?: string) => void;
  restoreFocus: (key?: string, fallbackElementId?: string) => boolean;
  announce: (message: string, priority?: "polite" | "assertive") => void;
}

const FocusManagerContext = createContext<FocusManagerContextValue | null>(null);

export const FocusManagerProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const savedFocusMapRef = useRef<Map<string, HTMLElement>>(new Map());
  const [politeMessage, setPoliteMessage] = useState<string>("");
  const [assertiveMessage, setAssertiveMessage] = useState<string>("");

  const saveFocus = useCallback((key: string = "default") => {
    if (typeof document !== "undefined" && document.activeElement instanceof HTMLElement) {
      savedFocusMapRef.current.set(key, document.activeElement);
    }
  }, []);

  const restoreFocus = useCallback((key: string = "default", fallbackElementId?: string): boolean => {
    const target = savedFocusMapRef.current.get(key);
    savedFocusMapRef.current.delete(key);

    if (target && typeof document !== "undefined" && document.body.contains(target)) {
      target.focus();
      return true;
    }

    if (fallbackElementId && typeof document !== "undefined") {
      const fallback = document.getElementById(fallbackElementId);
      if (fallback) {
        fallback.focus();
        return true;
      }
    }

    return false;
  }, []);

  const announce = useCallback((message: string, priority: "polite" | "assertive" = "polite") => {
    if (priority === "assertive") {
      setAssertiveMessage(message);
    } else {
      setPoliteMessage(message);
    }
  }, []);

  return (
    <FocusManagerContext.Provider value={{ saveFocus, restoreFocus, announce }}>
      {children}
      {/* Visually hidden live regions for screen-reader announcements */}
      <div
        id="a11y-live-polite"
        role="status"
        aria-live="polite"
        aria-atomic="true"
        style={{
          position: "absolute",
          width: "1px",
          height: "1px",
          padding: 0,
          margin: "-1px",
          overflow: "hidden",
          clip: "rect(0, 0, 0, 0)",
          whiteSpace: "nowrap",
          border: 0,
        }}
      >
        {politeMessage}
      </div>
      <div
        id="a11y-live-assertive"
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        style={{
          position: "absolute",
          width: "1px",
          height: "1px",
          padding: 0,
          margin: "-1px",
          overflow: "hidden",
          clip: "rect(0, 0, 0, 0)",
          whiteSpace: "nowrap",
          border: 0,
        }}
      >
        {assertiveMessage}
      </div>
    </FocusManagerContext.Provider>
  );
};

export function useFocusManager(): FocusManagerContextValue {
  const ctx = useContext(FocusManagerContext);
  if (!ctx) {
    throw new Error("useFocusManager must be used within a FocusManagerProvider");
  }
  return ctx;
}
