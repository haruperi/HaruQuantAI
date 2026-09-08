"use client";

import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
  type PropsWithChildren,
} from "react";
import { ArrowLeft, X } from "lucide-react";

import type { OverlayConfig } from "./contracts";

export interface OverlayFoundationProps extends PropsWithChildren<OverlayConfig> {
  readonly className?: string;
  readonly width?: number | string;
}

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function OverlayFoundation({
  isOpen,
  title,
  description,
  role = "dialog",
  closeOnEscape = true,
  closeOnBackdropClick = true,
  isDestructive = false,
  isDirty = false,
  initialFocusRef,
  returnFocusRef,
  onClose,
  onWarnUnsavedChanges,
  backNavigation,
  className = "",
  width = 560,
  children,
}: OverlayFoundationProps): React.JSX.Element | null {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const previouslyFocusedElementRef = useRef<HTMLElement | null>(null);
  const [showUnsavedPrompt, setShowUnsavedPrompt] = useState(false);

  // Safe dismiss request honoring unsaved changes
  const requestClose = useCallback(() => {
    if (isDirty) {
      if (onWarnUnsavedChanges) {
        const canProceed = onWarnUnsavedChanges();
        if (!canProceed) {
          setShowUnsavedPrompt(true);
          return;
        }
      } else {
        setShowUnsavedPrompt(true);
        return;
      }
    }
    setShowUnsavedPrompt(false);
    onClose();
  }, [isDirty, onWarnUnsavedChanges, onClose]);

  // Record activeElement before open, restore upon close
  useEffect(() => {
    if (isOpen) {
      previouslyFocusedElementRef.current =
        returnFocusRef?.current ?? (document.activeElement as HTMLElement | null);
    }
    return () => {
      if (previouslyFocusedElementRef.current && typeof previouslyFocusedElementRef.current.focus === "function") {
        previouslyFocusedElementRef.current.focus();
      }
    };
  }, [isOpen, returnFocusRef]);

  // Lock body scroll while open and restore on unmount
  useEffect(() => {
    if (!isOpen) return undefined;
    const priorOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = priorOverflow;
    };
  }, [isOpen]);

  // Set initial focus inside overlay
  useEffect(() => {
    if (!isOpen || !containerRef.current) return;
    const timer = setTimeout(() => {
      if (initialFocusRef?.current) {
        initialFocusRef.current.focus();
      } else {
        const focusable = containerRef.current?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
        if (focusable && focusable.length > 0) {
          focusable[0].focus();
        } else {
          containerRef.current?.focus();
        }
      }
    }, 10);
    return () => clearTimeout(timer);
  }, [isOpen, initialFocusRef]);

  // Keyboard accessibility: Escape handling & Focus Trap cycling
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === "Escape" && closeOnEscape) {
        event.preventDefault();
        event.stopPropagation();
        requestClose();
        return;
      }

      if (event.key === "Tab" && containerRef.current) {
        const focusable = Array.from(
          containerRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
        ).filter((el) => el.offsetParent !== null);

        if (focusable.length === 0) {
          event.preventDefault();
          return;
        }

        const firstElement = focusable[0];
        const lastElement = focusable[focusable.length - 1];

        if (event.shiftKey) {
          if (document.activeElement === firstElement || document.activeElement === containerRef.current) {
            event.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
          }
        }
      }
    },
    [closeOnEscape, requestClose],
  );

  if (!isOpen) return null;

  const isDrawer = role === "drawer";

  return (
    <div
      className={`overlay-foundation-backdrop ${isDrawer ? "drawer-backdrop" : ""}`}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.65)",
        backdropFilter: "blur(2px)",
        display: "flex",
        alignItems: isDrawer ? "stretch" : "center",
        justifyContent: isDrawer ? "flex-end" : "center",
        zIndex: 9000,
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && closeOnBackdropClick && !isDestructive) {
          requestClose();
        }
      }}
    >
      <div
        ref={containerRef}
        role={role === "alertdialog" ? "alertdialog" : "dialog"}
        aria-modal="true"
        aria-labelledby="overlay-title"
        aria-describedby={description ? "overlay-description" : undefined}
        tabIndex={-1}
        className={`overlay-container ${isDrawer ? "overlay-drawer" : "overlay-modal"} ${className}`}
        style={{
          width,
          maxWidth: isDrawer ? "100%" : "calc(100vw - 32px)",
          maxHeight: isDrawer ? "100vh" : "calc(100vh - 48px)",
          backgroundColor: "#161b22",
          border: "1px solid #30363d",
          borderRadius: isDrawer ? "0" : "8px",
          boxShadow: "0 16px 36px rgba(0, 0, 0, 0.5)",
          display: "flex",
          flexDirection: "column",
          outline: "none",
          position: "relative",
          color: "#e1e4ea",
        }}
        onKeyDown={handleKeyDown}
      >
        {/* Header Bar */}
        <header
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid #30363d",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            {/* Sequential Back Navigation replacing nested modals (MOD-005) */}
            {backNavigation?.canGoBack && (
              <button
                type="button"
                className="overlay-back-btn"
                aria-label={backNavigation.backLabel ?? "Go back"}
                onClick={backNavigation.onBack}
                style={{
                  background: "none",
                  border: "none",
                  color: "#58a6ff",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  padding: "4px",
                  borderRadius: "4px",
                }}
              >
                <ArrowLeft size={18} />
              </button>
            )}
            <div>
              <h2
                id="overlay-title"
                style={{
                  margin: 0,
                  fontSize: "18px",
                  fontWeight: 600,
                  color: isDestructive ? "#f85149" : "#fff",
                }}
              >
                {title}
              </h2>
              {description && (
                <p
                  id="overlay-description"
                  style={{
                    margin: "4px 0 0 0",
                    fontSize: "13px",
                    color: "#8b949e",
                  }}
                >
                  {description}
                </p>
              )}
            </div>
          </div>

          <button
            type="button"
            className="overlay-close-btn"
            aria-label="Close dialog"
            onClick={requestClose}
            style={{
              background: "none",
              border: "none",
              color: "#8b949e",
              cursor: "pointer",
              padding: "4px",
              borderRadius: "4px",
            }}
          >
            <X size={18} />
          </button>
        </header>

        {/* Content Body */}
        <div
          className="overlay-body"
          style={{
            padding: "20px",
            overflowY: "auto",
            flex: 1,
          }}
        >
          {children}
        </div>

        {/* Unsaved Changes Confirmation Prompt Modal Guard */}
        {showUnsavedPrompt && (
          <div
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="unsaved-prompt-title"
            aria-describedby="unsaved-prompt-desc"
            className="overlay-unsaved-guard"
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: "rgba(13, 17, 23, 0.92)",
              backdropFilter: "blur(3px)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              padding: "24px",
              zIndex: 9999,
              textAlign: "center",
            }}
          >
            <h3
              id="unsaved-prompt-title"
              style={{ margin: "0 0 8px 0", fontSize: "16px", color: "#f85149" }}
            >
              Discard unsaved changes?
            </h3>
            <p
              id="unsaved-prompt-desc"
              style={{ margin: "0 0 20px 0", fontSize: "13px", color: "#8b949e", maxWidth: "340px" }}
            >
              You have modified form fields in this draft. Leaving will discard all changes made during this session.
            </p>
            <div style={{ display: "flex", gap: "12px" }}>
              <button
                type="button"
                onClick={() => setShowUnsavedPrompt(false)}
                style={{
                  background: "#21262d",
                  border: "1px solid #30363d",
                  color: "#c9d1d9",
                  padding: "6px 14px",
                  borderRadius: "4px",
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                Keep Editing
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowUnsavedPrompt(false);
                  onClose();
                }}
                style={{
                  background: "#b62324",
                  border: "1px solid #f85149",
                  color: "#fff",
                  padding: "6px 14px",
                  borderRadius: "4px",
                  fontSize: "13px",
                  fontWeight: 500,
                  cursor: "pointer",
                }}
              >
                Discard &amp; Exit
              </button>
            </div>
          </div>
        )}

        {/* Restrained live announcements region for screen readers */}
        <div
          role="status"
          aria-live="polite"
          aria-atomic="true"
          style={{
            position: "absolute",
            width: 1,
            height: 1,
            padding: 0,
            margin: -1,
            overflow: "hidden",
            clip: "rect(0, 0, 0, 0)",
            whiteSpace: "nowrap",
            border: 0,
          }}
        >
          {showUnsavedPrompt ? "Warning: Unsaved changes detected." : title}
        </div>
      </div>
    </div>
  );
}
