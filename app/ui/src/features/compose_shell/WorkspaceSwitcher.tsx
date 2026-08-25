import React from "react";
import { useShellSnapshot, useUiRuntime } from "../../runtime/context";

export const WorkspaceSwitcher: React.FC = () => {
  const snapshot = useShellSnapshot();
  const bridge = useUiRuntime();

  const handleSelectWorkspace = (workspace_id: string) => {
    try {
      bridge.switchWorkspace(workspace_id);
    } catch (err) {
      console.error("Failed to switch workspace:", err);
    }
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLButtonElement>,
    currentIndex: number
  ) => {
    const workspaces = snapshot.available_workspaces;
    if (!workspaces.length) return;

    let targetIndex: number | null = null;

    switch (event.key) {
      case "Enter":
      case " ":
        event.preventDefault();
        handleSelectWorkspace(workspaces[currentIndex].workspace_id);
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
      handleSelectWorkspace(targetWorkspace.workspace_id);
      const tabElement = document.getElementById(
        `workspace-tab-${targetWorkspace.workspace_id}`
      );
      tabElement?.focus();
    }
  };

  if (!snapshot.available_workspaces.length) {
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
        {snapshot.available_workspaces.map((ws, index) => {
          const isActive = ws.workspace_id === snapshot.active_workspace_id;
          return (
            <li key={ws.workspace_id} role="presentation">
              <button
                type="button"
                role="tab"
                aria-selected={isActive}
                aria-controls={`workspace-panel-${ws.workspace_id}`}
                id={`workspace-tab-${ws.workspace_id}`}
                className={`workspace-tab-btn ${isActive ? "active" : ""}`}
                onClick={() => handleSelectWorkspace(ws.workspace_id)}
                onKeyDown={(e) => handleKeyDown(e, index)}
                tabIndex={isActive ? 0 : -1}
                data-testid={`workspace-tab-${ws.workspace_id}`}
              >
                {ws.icon_name && (
                  <span className="ws-icon" aria-hidden="true">
                    {ws.icon_name}
                  </span>
                )}
                <span className="ws-name">{ws.display_name}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
};
