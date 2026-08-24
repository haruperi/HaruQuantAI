import React from "react";
import { useShellSnapshot, useUiRuntime } from "../../runtime/context";

export const WorkspaceSwitcher: React.FC = () => {
  const snapshot = useShellSnapshot();
  const bridge = useUiRuntime();

  const handleSelectWorkspace = (workspaceId: string) => {
    try {
      bridge.switchWorkspace(workspaceId);
    } catch (err) {
      console.error("Failed to switch workspace:", err);
    }
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLButtonElement>,
    currentIndex: number
  ) => {
    const workspaces = snapshot.availableWorkspaces;
    if (!workspaces.length) return;

    let targetIndex: number | null = null;

    switch (event.key) {
      case "Enter":
      case " ":
        event.preventDefault();
        handleSelectWorkspace(workspaces[currentIndex].workspaceId);
        break;
      case "ArrowRight":
      case "ArrowDown":
        event.preventDefault();
        targetIndex = (currentIndex + 1) % workspaces.length;
        break;
      case "ArrowLeft":
      case "ArrowUp":
        event.preventDefault();
        targetIndex = (currentIndex - 1 + workspaces.length) % workspaces.length;
        break;
      case "Home":
        event.preventDefault();
        targetIndex = 0;
        break;
      case "End":
        event.preventDefault();
        targetIndex = workspaces.length - 1;
        break;
      default:
        break;
    }

    if (targetIndex !== null) {
      const targetWorkspace = workspaces[targetIndex];
      handleSelectWorkspace(targetWorkspace.workspaceId);
      const tabElement = document.getElementById(
        `workspace-tab-${targetWorkspace.workspaceId}`
      );
      tabElement?.focus();
    }
  };

  if (!snapshot.availableWorkspaces.length) {
    return (
      <nav aria-label="Workspaces" className="workspace-switcher-empty">
        <span role="status">No authorized workspaces available</span>
      </nav>
    );
  }

  return (
    <nav
      aria-label="Workspaces"
      className="workspace-switcher"
      data-testid="workspace-switcher"
    >
      <ul role="tablist" className="workspace-nav-list">
        {snapshot.availableWorkspaces.map((ws, index) => {
          const isActive = ws.workspaceId === snapshot.activeWorkspaceId;
          return (
            <li key={ws.workspaceId} role="presentation">
              <button
                type="button"
                role="tab"
                aria-selected={isActive}
                aria-controls={`workspace-panel-${ws.workspaceId}`}
                id={`workspace-tab-${ws.workspaceId}`}
                className={`workspace-tab-btn ${isActive ? "active" : ""}`}
                onClick={() => handleSelectWorkspace(ws.workspaceId)}
                onKeyDown={(e) => handleKeyDown(e, index)}
                tabIndex={isActive ? 0 : -1}
                data-testid={`workspace-tab-${ws.workspaceId}`}
              >
                {ws.iconName && (
                  <span className="ws-icon" aria-hidden="true">
                    {ws.iconName}
                  </span>
                )}
                <span className="ws-name">{ws.displayName}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
};
