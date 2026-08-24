import type { WorkspaceRoute } from "../../contracts/generated/ui_contracts";

export class RouteManager {
  /**
   * Restores an authorized, compatible route or returns a deterministic fallback.
   * Ensures removed/unauthorized routes cannot be resurrected from stale client state.
   */
  public static resolveRoute(
    requestedRoute: string,
    availableWorkspaces: readonly WorkspaceRoute[],
    defaultFallback: string = "/home"
  ): { targetRoute: string; activeWorkspace: WorkspaceRoute | null } {
    const matched = availableWorkspaces.find(
      (ws) => ws.routePath === requestedRoute && ws.isAuthorized !== false
    );

    if (matched) {
      return {
        targetRoute: matched.routePath,
        activeWorkspace: matched,
      };
    }

    const fallbackMatched = availableWorkspaces.find(
      (ws) => ws.routePath === defaultFallback && ws.isAuthorized !== false
    );

    return {
      targetRoute: defaultFallback,
      activeWorkspace: fallbackMatched ?? null,
    };
  }
}
