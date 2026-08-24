import React from "react";
import { useShellSnapshot, useActiveWorkspace } from "../../runtime/context";
import { WorkspaceSwitcher } from "./WorkspaceSwitcher";
import { CapabilityStateView } from "./CapabilityStateView";

export interface ShellProps {
  title?: string;
  showFooter?: boolean;
  headerSlot?: React.ReactNode;
  footerSlot?: React.ReactNode;
}

export const Shell: React.FC<ShellProps> = ({
  title = "HaruQuantAI",
  showFooter = true,
  headerSlot,
  footerSlot,
}) => {
  const snapshot = useShellSnapshot();
  const activeWorkspace = useActiveWorkspace();

  return (
    <div className="haru-shell-container" data-testid="app-shell">
      {/* 1. Header with branding & navigation */}
      <header className="shell-header" role="banner">
        <div className="header-brand">
          <h1 className="brand-title">{title}</h1>
        </div>
        <div className="header-nav">
          <WorkspaceSwitcher />
        </div>
        {headerSlot && <div className="header-slot">{headerSlot}</div>}
      </header>

      {/* 2. Global Capability & Status Bar */}
      <section
        className="shell-status-bar"
        aria-label="System status and capability readiness"
      >
        <div className="system-status-message" role="status">
          <span className="status-label">Status:</span>{" "}
          <span className="status-text">{snapshot.statusMessage}</span>
        </div>
        <div className="capability-badges-list">
          {Object.entries(snapshot.capabilityStates).map(([capId, state]) => (
            <CapabilityStateView key={capId} capabilityId={capId} state={state} />
          ))}
        </div>
      </section>

      {/* 3. Main Workspace Outlet */}
      <main
        className="shell-workspace-outlet"
        role="main"
        id={
          activeWorkspace
            ? `workspace-panel-${activeWorkspace.workspaceId}`
            : "workspace-panel-empty"
        }
        aria-labelledby={
          activeWorkspace
            ? `workspace-tab-${activeWorkspace.workspaceId}`
            : undefined
        }
        tabIndex={-1}
      >
        {activeWorkspace ? (
          <div className="active-workspace-wrapper">
            {activeWorkspace.renderWorkspace ? (
              activeWorkspace.renderWorkspace()
            ) : (
              <div className="workspace-placeholder" role="region">
                <h2>{activeWorkspace.displayName}</h2>
                <p>Route: {activeWorkspace.routePath}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="empty-workspace-view" role="status">
            <h2>No Active Workspace</h2>
            <p>Please select an available workspace from the navigation bar.</p>
          </div>
        )}
      </main>

      {/* 4. Optional Footer */}
      {showFooter && (
        <footer className="shell-footer" role="contentinfo">
          {footerSlot ? (
            footerSlot
          ) : (
            <div className="default-footer-content">
              <span>HaruQuantAI Composability Shell</span>
              <span>Route: {snapshot.currentRoute}</span>
            </div>
          )}
        </footer>
      )}
    </div>
  );
};
