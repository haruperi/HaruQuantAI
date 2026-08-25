import type { WorkspaceRoute } from "../../runtime/composition_bridge";

export class RouteManager {
  /**
   * Restores an authorized, compatible route or returns a deterministic fallback.
   * Ensures removed/unauthorized routes cannot be resurrected from stale client state.
   */
  public static resolveRoute(
    requestedRoute: string,
    available_workspaces: readonly WorkspaceRoute[],
    defaultFallback: string = "/home"
  ): { targetRoute: string; activeWorkspace: WorkspaceRoute | null } {
    const matched = available_workspaces.find(
      (ws) => ws.route_path === requestedRoute && ws.is_authorized !== false
    );

    if (matched) {
      return {
        targetRoute: matched.route_path,
        activeWorkspace: matched,
      };
    }

    const fallbackMatched = available_workspaces.find(
      (ws) => ws.route_path === defaultFallback && ws.is_authorized !== false
    );

    return {
      targetRoute: defaultFallback,
      activeWorkspace: fallbackMatched ?? null,
    };
  }
}
