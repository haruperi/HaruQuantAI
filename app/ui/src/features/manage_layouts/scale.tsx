/**
 * View scale controls for FEAT-UI-MANAGE_LAYOUTS (FR-UI-SCALE_VIEWS).
 *
 * Global zoom and fullscreen, presented in the shared header via the
 * compose-shell's public `render(headerSlot)` parameter (composition at the
 * root; no cross-feature imports). Zoom is bounded to [MIN_SCALE, MAX_SCALE]
 * so safety-relevant header/status chrome stays fully readable — scale
 * applies only to the registered workspace outlet.
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

export const MIN_SCALE = 0.75;
export const MAX_SCALE = 1.5;
const SCALE_STEP = 0.25;

export function clampScale(value: number): number {
  if (Number.isNaN(value)) return 1;
  return Math.min(MAX_SCALE, Math.max(MIN_SCALE, Math.round(value * 100) / 100));
}

export interface ViewScaleContextValue {
  readonly scale: number;
  readonly zoomIn: () => void;
  readonly zoomOut: () => void;
  readonly resetZoom: () => void;
  readonly toggleFullscreen: () => void;
  readonly isFullscreen: boolean;
  readonly registerOutlet: (element: HTMLElement | null) => void;
}

const ViewScaleContext = createContext<ViewScaleContextValue | null>(null);

export const ViewScaleProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [scale, setScale] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const outletRef = useRef<HTMLElement | null>(null);

  // Zoom applies only to the workstation outlet(s); header/status chrome is
  // never scaled (FR-UI-SCALE_VIEWS minimum-region acceptance).
  useEffect(() => {
    document.documentElement.style.setProperty(
      "--haru-workstation-scale",
      String(scale)
    );
    const styleId = "haru-workstation-scale-rule";
    if (!document.getElementById(styleId)) {
      const rule = document.createElement("style");
      rule.id = styleId;
      rule.textContent =
        "main, [data-testid='workspace-host'] { zoom: var(--haru-workstation-scale, 1); }";
      document.head.appendChild(rule);
    }
  }, [scale]);

  const zoomIn = useCallback(() => setScale((s) => clampScale(s + SCALE_STEP)), []);
  const zoomOut = useCallback(() => setScale((s) => clampScale(s - SCALE_STEP)), []);
  const resetZoom = useCallback(() => setScale(1), []);

  const toggleFullscreen = useCallback(() => {
    const outlet = outletRef.current;
    if (!outlet) return;
    if (document.fullscreenElement) {
      void document.exitFullscreen().catch(() => undefined);
    } else {
      void outlet.requestFullscreen().catch(() => undefined);
    }
  }, []);

  const registerOutlet = useCallback((element: HTMLElement | null) => {
    outletRef.current = element;
    if (element) {
      element.onfullscreenchange = () => {
        setIsFullscreen(document.fullscreenElement === element);
      };
    }
  }, []);

  const value = useMemo<ViewScaleContextValue>(
    () => ({
      scale,
      zoomIn,
      zoomOut,
      resetZoom,
      toggleFullscreen,
      isFullscreen,
      registerOutlet,
    }),
    [scale, zoomIn, zoomOut, resetZoom, toggleFullscreen, isFullscreen, registerOutlet]
  );

  return (
    <ViewScaleContext.Provider value={value}>{children}</ViewScaleContext.Provider>
  );
};

export function useViewScale(): ViewScaleContextValue {
  const context = useContext(ViewScaleContext);
  if (!context) {
    throw new Error("useViewScale must be used within a ViewScaleProvider");
  }
  return context;
}

/** Header controls rendered through the compose-shell public header slot. */
export const ScaleControls: React.FC = () => {
  const { scale, zoomIn, zoomOut, resetZoom, toggleFullscreen, isFullscreen } =
    useViewScale();

  const buttonStyle: React.CSSProperties = {
    padding: "4px 10px",
    backgroundColor: "#1e293b",
    color: "#e2e8f0",
    border: "1px solid #475569",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "12px",
  };

  return (
    <div
      role="toolbar"
      aria-label="View scale controls"
      style={{ display: "flex", gap: "6px", alignItems: "center" }}
    >
      <button type="button" data-testid="scale-zoom-out" onClick={zoomOut} style={buttonStyle} aria-label="Zoom out">
        −
      </button>
      <button
        type="button"
        data-testid="scale-reset"
        onClick={resetZoom}
        style={{ ...buttonStyle, minWidth: "52px" }}
        aria-label={`Reset zoom (currently ${Math.round(scale * 100)}%)`}
      >
        {Math.round(scale * 100)}%
      </button>
      <button type="button" data-testid="scale-zoom-in" onClick={zoomIn} style={buttonStyle} aria-label="Zoom in">
        +
      </button>
      <button
        type="button"
        data-testid="scale-fullscreen"
        onClick={toggleFullscreen}
        style={buttonStyle}
        aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
      >
        {isFullscreen ? "⛶ Exit" : "⛶ Full"}
      </button>
    </div>
  );
};
