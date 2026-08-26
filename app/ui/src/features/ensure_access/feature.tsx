/**
 * FEAT-UI-ENSURE_ACCESS feature instance (Completable slice: FR-UI-MANAGE_FOCUS,
 * FR-UI-DISTINGUISH_STATE).
 *
 * Registers the `ui.ensure-access@1` capability manifest, coordinates route and
 * workspace outlet focus transitions, and provides the focus management context.
 */

import React, { useEffect, useRef } from "react";
import type { ReactNode } from "react";
import type { UiFeatureInstance } from "../../runtime/composition_bridge";
import { SPEC } from "./manifest";
import { parseEnsureAccessConfig, type EnsureAccessConfig } from "./config";
import { FocusManagerProvider, useFocusManager } from "../../context/focus";
import { useShellSnapshot } from "../../runtime/context";

const RouteFocusCoordinator: React.FC = () => {
  const snapshot = useShellSnapshot();
  const { focusElementById } = useFocusManager();
  const prevTargetKeyRef = useRef<string | null>(null);

  useEffect(() => {
    const targetOutletId = snapshot.active_workspace_id
      ? `workspace-panel-${snapshot.active_workspace_id}`
      : "workspace-panel-empty";

    const targetKey = `${snapshot.current_route}:${snapshot.active_workspace_id ?? "empty"}`;
    if (prevTargetKeyRef.current !== targetKey) {
      prevTargetKeyRef.current = targetKey;
      focusElementById(targetOutletId);
    }
  }, [snapshot.current_route, snapshot.active_workspace_id, focusElementById]);

  return null;
};

export interface EnsureAccessProviderProps {
  readonly children: ReactNode;
}

export const EnsureAccessProvider: React.FC<EnsureAccessProviderProps> = ({ children }) => {
  return (
    <FocusManagerProvider>
      <RouteFocusCoordinator />
      {children}
    </FocusManagerProvider>
  );
};

export class EnsureAccessFeature implements UiFeatureInstance {
  public readonly manifest = SPEC;
  public readonly config: EnsureAccessConfig;

  constructor(config?: Record<string, unknown>) {
    this.config = parseEnsureAccessConfig(config);
  }

  public renderProvider(children: ReactNode): ReactNode {
    return <EnsureAccessProvider>{children}</EnsureAccessProvider>;
  }
}

export function createFeature(config?: Record<string, unknown>): EnsureAccessFeature {
  return new EnsureAccessFeature(config);
}
