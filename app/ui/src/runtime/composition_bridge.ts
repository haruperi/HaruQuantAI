/**
 * UI Runtime Composition Bridge.
 * Bridges backend capabilities to typed React presentation components without static service coupling.
 */

import type {
  CapabilityPresentationState,
  ShellSnapshot,
  WorkspaceRoute,
} from "../contracts/generated/ui_contracts";

export interface UiFeatureManifest {
  readonly featureId: string;
  readonly name: string;
  readonly description: string;
  readonly providesCapabilities?: readonly string[];
  readonly requiredCapabilities?: readonly string[];
  readonly optionalCapabilities?: readonly string[];
  readonly contributedWorkspaces?: readonly WorkspaceRoute[];
}

export interface UiFeatureInstance {
  readonly manifest: UiFeatureManifest;
  mount?: () => void | Promise<void>;
  unmount?: () => void | Promise<void>;
}

export interface UiCompositionBridgeOptions {
  readonly syncBrowserUrl?: boolean;
}

export class UiCompositionBridge {
  private readonly registeredFeatures = new Map<string, UiFeatureInstance>();
  private readonly activeCapabilities = new Set<string>();
  private readonly loadingCapabilities = new Set<string>();
  private readonly degradedCapabilities = new Set<string>();
  private readonly disabledCapabilities = new Set<string>();
  private readonly unauthorizedCapabilities = new Set<string>();
  private readonly incompatibleCapabilities = new Set<string>();
  private readonly listeners = new Set<() => void>();

  private activeWorkspaceId: string | null = null;
  private currentRoute: string = "/home";
  private statusMessage: string = "Ready";
  private readonly syncBrowserUrl: boolean;
  private popStateDisposer: (() => void) | null = null;

  constructor(options: UiCompositionBridgeOptions = {}) {
    this.syncBrowserUrl = options.syncBrowserUrl ?? true;
    this.initHistorySync();
  }

  private initHistorySync(): void {
    if (this.syncBrowserUrl && typeof window !== "undefined" && typeof window.addEventListener === "function") {
      const handlePopState = () => {
        this.restoreRoute(window.location.pathname, "/home", false);
      };
      window.addEventListener("popstate", handlePopState);
      this.popStateDisposer = () => {
        window.removeEventListener("popstate", handlePopState);
      };
    }
  }

  public destroy(): void {
    if (this.popStateDisposer) {
      this.popStateDisposer();
      this.popStateDisposer = null;
    }
    this.listeners.clear();
  }

  public registerFeature(feature: UiFeatureInstance): () => void {
    this.registeredFeatures.set(feature.manifest.featureId, feature);
    if (feature.manifest.providesCapabilities) {
      for (const cap of feature.manifest.providesCapabilities) {
        this.activeCapabilities.add(cap);
      }
    }
    feature.mount?.();
    this.notify();

    return () => {
      this.unregisterFeature(feature.manifest.featureId);
    };
  }

  public unregisterFeature(featureId: string): void {
    const feature = this.registeredFeatures.get(featureId);
    if (!feature) return;

    if (feature.manifest.providesCapabilities) {
      for (const cap of feature.manifest.providesCapabilities) {
        this.activeCapabilities.delete(cap);
      }
    }
    feature.unmount?.();
    this.registeredFeatures.delete(featureId);
    this.notify();
  }

  public setCapabilityState(
    capabilityId: string,
    state: CapabilityPresentationState
  ): void {
    this.activeCapabilities.delete(capabilityId);
    this.loadingCapabilities.delete(capabilityId);
    this.degradedCapabilities.delete(capabilityId);
    this.disabledCapabilities.delete(capabilityId);
    this.unauthorizedCapabilities.delete(capabilityId);
    this.incompatibleCapabilities.delete(capabilityId);

    switch (state) {
      case "ready":
        this.activeCapabilities.add(capabilityId);
        break;
      case "loading":
        this.loadingCapabilities.add(capabilityId);
        break;
      case "degraded":
        this.degradedCapabilities.add(capabilityId);
        break;
      case "disabled":
        this.disabledCapabilities.add(capabilityId);
        break;
      case "unauthorized":
        this.unauthorizedCapabilities.add(capabilityId);
        break;
      case "incompatible":
        this.incompatibleCapabilities.add(capabilityId);
        break;
      case "unavailable":
      default:
        break;
    }
    this.notify();
  }

  public getCapabilityPresentationState(
    capabilityId: string
  ): CapabilityPresentationState {
    if (this.unauthorizedCapabilities.has(capabilityId)) return "unauthorized";
    if (this.incompatibleCapabilities.has(capabilityId)) return "incompatible";
    if (this.disabledCapabilities.has(capabilityId)) return "disabled";
    if (this.degradedCapabilities.has(capabilityId)) return "degraded";
    if (this.loadingCapabilities.has(capabilityId)) return "loading";
    if (this.activeCapabilities.has(capabilityId)) return "ready";
    return "unavailable";
  }

  public discoverWorkspaces(): readonly WorkspaceRoute[] {
    const candidateRoutes: WorkspaceRoute[] = [];

    for (const feature of this.registeredFeatures.values()) {
      if (feature.manifest.contributedWorkspaces) {
        for (const ws of feature.manifest.contributedWorkspaces) {
          if (ws.isAuthorized === false) continue;

          const required = ws.requiredCapabilities ?? [];
          const isCompatible = required.every((cap) =>
            this.activeCapabilities.has(cap)
          );

          if (isCompatible) {
            candidateRoutes.push(ws);
          }
        }
      }
    }
    return candidateRoutes;
  }

  public switchWorkspace(targetWorkspaceId: string, updateHistory: boolean = true): void {
    const available = this.discoverWorkspaces();
    const target = available.find((ws) => ws.workspaceId === targetWorkspaceId);

    if (!target) {
      throw new Error(
        `Workspace '${targetWorkspaceId}' is unavailable or unauthorized`
      );
    }

    this.activeWorkspaceId = targetWorkspaceId;
    this.currentRoute = target.routePath;
    this.statusMessage = `Active workspace: ${target.displayName}`;

    if (updateHistory && this.syncBrowserUrl && typeof window !== "undefined" && typeof window.history?.pushState === "function") {
      if (window.location.pathname !== target.routePath) {
        window.history.pushState({ workspaceId: targetWorkspaceId }, "", target.routePath);
      }
    }

    this.notify();
  }

  public restoreRoute(
    requestedRoute: string,
    defaultFallback: string = "/home",
    updateHistory: boolean = true
  ): string {
    const available = this.discoverWorkspaces();
    const match = available.find((ws) => ws.routePath === requestedRoute);

    if (match) {
      this.activeWorkspaceId = match.workspaceId;
      this.currentRoute = match.routePath;
      this.statusMessage = `Active workspace: ${match.displayName}`;

      if (updateHistory && this.syncBrowserUrl && typeof window !== "undefined" && typeof window.history?.replaceState === "function") {
        if (window.location.pathname !== match.routePath) {
          window.history.replaceState({ workspaceId: match.workspaceId }, "", match.routePath);
        }
      }

      this.notify();
      return match.routePath;
    }

    this.activeWorkspaceId = null;
    this.currentRoute = defaultFallback;
    this.statusMessage = `Route fallback to ${defaultFallback}`;

    if (updateHistory && this.syncBrowserUrl && typeof window !== "undefined" && typeof window.history?.replaceState === "function") {
      if (window.location.pathname !== defaultFallback) {
        window.history.replaceState({}, "", defaultFallback);
      }
    }

    this.notify();
    return defaultFallback;
  }

  public getSnapshot(): ShellSnapshot {
    const available = this.discoverWorkspaces();
    const capabilityStates: Record<string, CapabilityPresentationState> = {};

    for (const feature of this.registeredFeatures.values()) {
      const required = feature.manifest.requiredCapabilities ?? [];
      const optional = feature.manifest.optionalCapabilities ?? [];
      const all = [...required, ...optional];
      for (const cap of all) {
        capabilityStates[cap] = this.getCapabilityPresentationState(cap);
      }
    }

    const isReady =
      !Array.from(this.loadingCapabilities).length &&
      (this.activeWorkspaceId !== null || available.length > 0);

    return {
      activeWorkspaceId: this.activeWorkspaceId,
      currentRoute: this.currentRoute,
      availableWorkspaces: available,
      capabilityStates,
      isReady,
      statusMessage: this.statusMessage,
    };
  }

  public subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notify(): void {
    for (const listener of this.listeners) {
      listener();
    }
  }
}
