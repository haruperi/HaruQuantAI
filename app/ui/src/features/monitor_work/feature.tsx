/**
 * FEAT-UI-MONITOR_WORK feature instance (Completable slice: FR-UI-TRACK_PROGRESS,
 * FR-UI-STREAM_ACTIVITY, FR-UI-PRESENT_FAILURES).
 *
 * Registers the `ui.monitor-work@1` capability manifest and provides the
 * presentation client and activity snapshot context to owned widgets.
 */

import React, { createContext, useContext } from "react";
import type { ReactNode } from "react";
import type { UiFeatureInstance } from "../../runtime/composition_bridge";
import type { IUiPresentationClient } from "../../clients/ui_client";
import { SPEC } from "./manifest";
import type { ActivitySnapshot } from "./activity_model";

interface MonitorWorkContextValue {
  readonly client: IUiPresentationClient;
  readonly activitySnapshot: ActivitySnapshot | null;
}

const MonitorWorkContext = createContext<MonitorWorkContextValue | null>(null);

export interface MonitorWorkClientProviderProps {
  readonly client: IUiPresentationClient;
  readonly activitySnapshot?: ActivitySnapshot | null;
  readonly children: ReactNode;
}

export const MonitorWorkClientProvider: React.FC<MonitorWorkClientProviderProps> = ({
  client,
  activitySnapshot = null,
  children,
}) => {
  const value: MonitorWorkContextValue = {
    client,
    activitySnapshot: activitySnapshot ?? null,
  };

  return (
    <MonitorWorkContext.Provider value={value}>
      {children}
    </MonitorWorkContext.Provider>
  );
};

export function useMonitorWorkClient(): IUiPresentationClient {
  const ctx = useContext(MonitorWorkContext);
  if (!ctx) {
    throw new Error(
      "useMonitorWorkClient must be used within a MonitorWorkClientProvider"
    );
  }
  return ctx.client;
}

export function useActivitySnapshot(): ActivitySnapshot | null {
  const ctx = useContext(MonitorWorkContext);
  if (!ctx) {
    throw new Error(
      "useActivitySnapshot must be used within a MonitorWorkClientProvider"
    );
  }
  return ctx.activitySnapshot;
}

export interface MonitorWorkFeatureOptions {
  readonly presentationClient: IUiPresentationClient;
  readonly activitySnapshot?: ActivitySnapshot | null;
}

export class MonitorWorkFeature implements UiFeatureInstance {
  public readonly manifest = SPEC;
  private readonly presentationClient: IUiPresentationClient;
  private readonly activitySnapshot: ActivitySnapshot | null;

  constructor(options: MonitorWorkFeatureOptions) {
    this.presentationClient = options.presentationClient;
    this.activitySnapshot = options.activitySnapshot ?? null;
  }

  public renderClientProvider(
    children: ReactNode,
    snapshotOverride?: ActivitySnapshot
  ): ReactNode {
    return (
      <MonitorWorkClientProvider
        client={this.presentationClient}
        activitySnapshot={snapshotOverride ?? this.activitySnapshot}
      >
        {children}
      </MonitorWorkClientProvider>
    );
  }
}

export function createFeature(
  options: MonitorWorkFeatureOptions
): MonitorWorkFeature {
  return new MonitorWorkFeature(options);
}
