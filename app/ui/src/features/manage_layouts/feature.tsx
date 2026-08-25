/**
 * FEAT-UI-MANAGE_LAYOUTS feature instance.
 *
 * Owns layout templates, persistence, view scale, and the
 * `workspace_templates` widget. Contributes no workspaces — it enhances the
 * existing workstation hosts through a layout controller (template manager +
 * persistence + template request bus) passed in at the composition root.
 */

import React, { createContext, useContext } from "react";
import type { ReactNode } from "react";
import type { UiFeatureInstance } from "../../runtime/composition_bridge";
import { TemplateManager } from "../../workspaces/template_manager";
import type { IUiPresentationClient } from "../../clients/ui_client";
import { SPEC } from "./manifest";
import { parseManageLayoutsConfig, type ManageLayoutsConfig } from "./config";
import { buildTemplateManager } from "./templates";
import { createLayoutPersistence, type LayoutPersistence } from "./persistence";

/**
 * Feature-owned template request bus: the `workspace_templates` widget
 * requests a template application; workstation hosts subscribed via the
 * layout controller apply it through the engine's TemplateManager.
 */
export type TemplateRequestListener = (templateId: string) => void;

export interface TemplateRequestBus {
  emit(templateId: string): void;
  subscribe(listener: TemplateRequestListener): () => void;
}

export function createTemplateRequestBus(): TemplateRequestBus {
  const listeners = new Set<TemplateRequestListener>();
  return {
    emit(templateId) {
      for (const listener of listeners) {
        listener(templateId);
      }
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
  };
}

/**
 * Shared template request bus for this feature: the `workspace_templates`
 * widget emits here; workstation hosts (wired at the composition root)
 * subscribe and apply through the engine's TemplateManager.
 */
export const manageLayoutsTemplateRequestBus: TemplateRequestBus =
  createTemplateRequestBus();

/** Layout controller handed to workstation hosts at the composition root. */
export interface LayoutController {
  readonly templateManager: TemplateManager;
  readonly persistence: LayoutPersistence;
  readonly templateRequests: TemplateRequestBus;
}

/** Presentation-client context owned by FEAT-UI-MANAGE_LAYOUTS. */
const ManageLayoutsClientContext = createContext<IUiPresentationClient | null>(null);

export interface ManageLayoutsClientProviderProps {
  readonly client: IUiPresentationClient;
  readonly children: ReactNode;
}

export const ManageLayoutsClientProvider: React.FC<
  ManageLayoutsClientProviderProps
> = ({ client, children }) => (
  <ManageLayoutsClientContext.Provider value={client}>
    {children}
  </ManageLayoutsClientContext.Provider>
);

export function useManageLayoutsClient(): IUiPresentationClient {
  const client = useContext(ManageLayoutsClientContext);
  if (!client) {
    throw new Error(
      "useManageLayoutsClient must be used within a ManageLayoutsClientProvider"
    );
  }
  return client;
}

export class ManageLayoutsFeature implements UiFeatureInstance {
  public readonly manifest = SPEC;
  public readonly config: ManageLayoutsConfig;
  public readonly layoutController: LayoutController;
  private readonly presentationClient: IUiPresentationClient;

  constructor(options: {
    readonly presentationClient: IUiPresentationClient;
    readonly config?: Record<string, unknown>;
  }) {
    this.config = parseManageLayoutsConfig(options.config);
    this.presentationClient = options.presentationClient;
    this.layoutController = {
      templateManager: buildTemplateManager(),
      persistence: createLayoutPersistence({
        schemaVersion: this.config.layoutSchemaVersion,
        maxRestoredTabs: this.config.maxRestoredTabs,
      }),
      templateRequests: manageLayoutsTemplateRequestBus,
    };
  }

  public renderClientProvider(children: ReactNode): ReactNode {
    return (
      <ManageLayoutsClientProvider client={this.presentationClient}>
        {children}
      </ManageLayoutsClientProvider>
    );
  }
}

export function createFeature(options: {
  readonly presentationClient: IUiPresentationClient;
  readonly config?: Record<string, unknown>;
}): ManageLayoutsFeature {
  return new ManageLayoutsFeature(options);
}
