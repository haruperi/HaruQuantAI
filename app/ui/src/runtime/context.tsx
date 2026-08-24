import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useMemo,
  type ReactNode,
} from "react";
import { UiCompositionBridge } from "./composition_bridge";
import type {
  CapabilityPresentationState,
  ShellSnapshot,
} from "../contracts/generated/ui_contracts";

const UiRuntimeContext = createContext<UiCompositionBridge | null>(null);

export interface UiRuntimeProviderProps {
  bridge: UiCompositionBridge;
  children: ReactNode;
}

export const UiRuntimeProvider: React.FC<UiRuntimeProviderProps> = ({
  bridge,
  children,
}) => {
  return (
    <UiRuntimeContext.Provider value={bridge}>
      {children}
    </UiRuntimeContext.Provider>
  );
};

export function useUiRuntime(): UiCompositionBridge {
  const bridge = useContext(UiRuntimeContext);
  if (!bridge) {
    throw new Error("useUiRuntime must be used within a UiRuntimeProvider");
  }
  return bridge;
}

export function useShellSnapshot(): ShellSnapshot {
  const bridge = useUiRuntime();
  const [snapshot, setSnapshot] = useState<ShellSnapshot>(() =>
    bridge.getSnapshot()
  );

  useEffect(() => {
    setSnapshot(bridge.getSnapshot());
    const unsubscribe = bridge.subscribe(() => {
      setSnapshot(bridge.getSnapshot());
    });
    return unsubscribe;
  }, [bridge]);

  return snapshot;
}

export function useCapabilityState(
  capabilityId: string
): CapabilityPresentationState {
  const bridge = useUiRuntime();
  const [state, setState] = useState<CapabilityPresentationState>(() =>
    bridge.getCapabilityPresentationState(capabilityId)
  );

  useEffect(() => {
    setState(bridge.getCapabilityPresentationState(capabilityId));
    const unsubscribe = bridge.subscribe(() => {
      setState(bridge.getCapabilityPresentationState(capabilityId));
    });
    return unsubscribe;
  }, [bridge, capabilityId]);

  return state;
}

export function useActiveWorkspace() {
  const snapshot = useShellSnapshot();
  const activeWorkspace = useMemo(() => {
    return (
      snapshot.availableWorkspaces.find(
        (ws) => ws.workspaceId === snapshot.activeWorkspaceId
      ) ?? null
    );
  }, [snapshot.availableWorkspaces, snapshot.activeWorkspaceId]);

  return activeWorkspace;
}
