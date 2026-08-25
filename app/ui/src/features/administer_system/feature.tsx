/**
 * FEAT-UI-ADMINISTER_SYSTEM feature instance (Completable slice: FR-UI-SET_APPEARANCE,
 * FR-UI-CONFIGURE_CLIENT, FR-UI-MANAGE_LICENSE).
 *
 * Registers the `ui.administer-system@1` capability manifest and provides the
 * presentation client context to owned widgets.
 */

import React, { createContext, useContext } from "react";
import type { ReactNode } from "react";
import type { UiFeatureInstance } from "../../runtime/composition_bridge";
import type { IUiPresentationClient } from "../../clients/ui_client";
import { SPEC } from "./manifest";

interface AdministerSystemContextValue {
  readonly client: IUiPresentationClient;
}

const AdministerSystemContext = createContext<AdministerSystemContextValue | null>(null);

export interface AdministerSystemClientProviderProps {
  readonly client: IUiPresentationClient;
  readonly children: ReactNode;
}

export const AdministerSystemClientProvider: React.FC<AdministerSystemClientProviderProps> = ({
  client,
  children,
}) => {
  const value: AdministerSystemContextValue = {
    client,
  };

  return (
    <AdministerSystemContext.Provider value={value}>
      {children}
    </AdministerSystemContext.Provider>
  );
};

export function useAdministerSystemClient(): IUiPresentationClient {
  const ctx = useContext(AdministerSystemContext);
  if (!ctx) {
    throw new Error(
      "useAdministerSystemClient must be used within an AdministerSystemClientProvider"
    );
  }
  return ctx.client;
}

export interface AdministerSystemFeatureOptions {
  readonly presentationClient: IUiPresentationClient;
}

export class AdministerSystemFeature implements UiFeatureInstance {
  public readonly manifest = SPEC;
  private readonly presentationClient: IUiPresentationClient;

  constructor(options: AdministerSystemFeatureOptions) {
    this.presentationClient = options.presentationClient;
  }

  public renderClientProvider(children: ReactNode): ReactNode {
    return (
      <AdministerSystemClientProvider client={this.presentationClient}>
        {children}
      </AdministerSystemClientProvider>
    );
  }
}

export function createFeature(
  options: AdministerSystemFeatureOptions
): AdministerSystemFeature {
  return new AdministerSystemFeature(options);
}
