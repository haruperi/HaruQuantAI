/**
 * Accessibility and Focus Management Context for HaruQuantAI D-UI.
 *
 * Implements FEAT-UI-ENSURE_ACCESS foundation:
 * - Focus saving and restoration across dialogs, view replacements, and panel removals
 * - Rejection of detached, hidden, inert, or disabled focus targets with deterministic fallback
 * - Screen-reader live region announcements (polite status and assertive error/failure notices)
 * - Deterministic programmatic focus target validation and route/workspace coordination
 */

import React, {
  createContext,
  useContext,
  useState,
  useRef,
  useCallback,
  type ReactNode,
} from "react";

export interface FocusManagerContextValue {
  saveFocus: (key?: string) => void;
  restoreFocus: (key?: string, fallbackElementId?: string) => boolean;
  focusElementById: (elementId: string) => boolean;
  announce: (message: string, priority?: "polite" | "assertive") => void;
}

const FocusManagerContext = createContext<FocusManagerContextValue | null>(null);

/**
 * Validates that an element is a genuine, accessible, and focusable target in the DOM.
 * Rejects detached, hidden, aria-hidden, inert, and disabled elements.
 */
export function isElementValidFocusTarget(el: HTMLElement | null): boolean {
  if (!el) return false;
  if (typeof document === "undefined") return false;
  if (!document.body.contains(el)) return false;

  // Rejects disabled elements (e.g. <button disabled>)
  if (el.hasAttribute("disabled") || (el as HTMLButtonElement).disabled === true) {
    return false;
  }

  // Rejects inert elements
  if (el.hasAttribute("inert") || (el as HTMLElement & { inert?: boolean }).inert === true) {
    return false;
  }

  // Rejects hidden elements or aria-hidden elements
  if (el.hasAttribute("hidden") || el.getAttribute("aria-hidden") === "true") {
    return false;
  }

  // Rejects elements inside a hidden, aria-hidden, or inert ancestor
  const hiddenAncestor = el.closest('[hidden], [aria-hidden="true"], [inert]');
  if (hiddenAncestor && hiddenAncestor !== el) {
    return false;
  }

  // Rejects elements explicitly styled with display: none or visibility: hidden
  if (el.style.display === "none" || el.style.visibility === "hidden") {
    return false;
  }

  return true;
}

export const FocusManagerProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const savedFocusMapRef = useRef<Map<string, HTMLElement>>(new Map());
  const [politeMessage, setPoliteMessage] = useState<string>("");
  const [assertiveMessage, setAssertiveMessage] = useState<string>("");

  const saveFocus = useCallback((key: string = "default") => {
    if (typeof document !== "undefined" && document.activeElement instanceof HTMLElement) {
      if (isElementValidFocusTarget(document.activeElement)) {
        savedFocusMapRef.current.set(key, document.activeElement);
      }
    }
  }, []);

  const restoreFocus = useCallback((key: string = "default", fallbackElementId?: string): boolean => {
    const target = savedFocusMapRef.current.get(key);
    savedFocusMapRef.current.delete(key);

    if (target && isElementValidFocusTarget(target)) {
      target.focus();
      if (typeof document !== "undefined" && document.activeElement === target) {
        return true;
      }
    }

    if (fallbackElementId && typeof document !== "undefined") {
      const fallback = document.getElementById(fallbackElementId);
      if (fallback && isElementValidFocusTarget(fallback)) {
        fallback.focus();
        if (document.activeElement === fallback) {
          return true;
        }
      }
    }

    return false;
  }, []);

  const focusElementById = useCallback((elementId: string): boolean => {
    if (typeof document === "undefined") return false;
    const target = document.getElementById(elementId);
    if (target && isElementValidFocusTarget(target)) {
      target.focus();
      return document.activeElement === target;
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
    <FocusManagerContext.Provider
      value={{ saveFocus, restoreFocus, focusElementById, announce }}
    >
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
