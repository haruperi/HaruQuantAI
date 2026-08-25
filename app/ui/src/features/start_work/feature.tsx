/**
 * FEAT-UI-START_WORK feature instance.
 *
 * Owns the Home landing workspace (`/home`) with capability-aware entry
 * points (FR-UI-PRESENT_HOME) and the product-news surface
 * (FR-UI-SHOW_PRODUCT_NEWS). Also contributes the research/data workstation
 * routes previously registered through the placeholder manifest.
 */

import React, { createContext, useContext } from "react";
import type { ReactNode } from "react";
import type { UiFeatureInstance } from "../../runtime/composition_bridge";
import type { WorkspaceLayoutSnapshot } from "../../contracts/generated/ui";
import { WidgetRegistry } from "../../runtime/widget_registry";
import { WorkspaceHost } from "../../workspaces/WorkspaceHost";
import type { IUiPresentationClient } from "../../clients/ui_client";
import { SPEC } from "./manifest";
import { parseStartWorkConfig, type StartWorkConfig } from "./config";

/**
 * Presentation-client context owned by FEAT-UI-START_WORK.
 * Injects the start-work capability client into the owned widgets without
 * static service coupling; the dev runtime supplies the mock provider.
 */
const StartWorkClientContext = createContext<IUiPresentationClient | null>(null);

export interface StartWorkClientProviderProps {
  readonly client: IUiPresentationClient;
  readonly children: ReactNode;
}

export const StartWorkClientProvider: React.FC<StartWorkClientProviderProps> = ({
  client,
  children,
}) => {
  return (
    <StartWorkClientContext.Provider value={client}>
      {children}
    </StartWorkClientContext.Provider>
  );
};

export function useStartWorkClient(): IUiPresentationClient {
  const client = useContext(StartWorkClientContext);
  if (!client) {
    throw new Error(
      "useStartWorkClient must be used within a StartWorkClientProvider"
    );
  }
  return client;
}

function createHomeLayout(): WorkspaceLayoutSnapshot {
  const createdAt = Date.now();
  return {
    layout_id: `layout-start-work-home-${createdAt}`,
    workspace_id: "workstation-main",
    actor_id: "system",
    layout_version: 1,
    capability_snapshot_id: "snap-start-work-home",
    widget_instances: [
      {
        instance_id: `inst-home-${createdAt}`,
        widget_type: "home",
        workspace_id: "workstation-main",
        configuration_version: 1,
        state_version: 1,
        schema_version: 1,
      },
      {
        instance_id: `inst-product-news-${createdAt}`,
        widget_type: "product_news",
        workspace_id: "workstation-main",
        configuration_version: 1,
        state_version: 1,
        schema_version: 1,
      },
    ],
    placements: [
      {
        instance_id: `inst-home-${createdAt}`,
        panel_id: "panel-home-left",
        panel_order: 0,
        tab_order: 0,
        size_ratio: "0.7",
        schema_version: 1,
      },
      {
        instance_id: `inst-product-news-${createdAt}`,
        panel_id: "panel-home-right",
        panel_order: 1,
        tab_order: 0,
        size_ratio: "0.3",
        schema_version: 1,
      },
    ],
    active_panel_id: `inst-home-${createdAt}`,
    content_hash: "start-work-home-layout",
    schema_version: 1,
  };
}

export interface StartWorkFeatureOptions {
  readonly presentationClient: IUiPresentationClient;
  readonly widgetRegistry: WidgetRegistry;
  readonly config?: Record<string, unknown>;
}

export class StartWorkFeature implements UiFeatureInstance {
  public readonly manifest: UiFeatureInstance["manifest"];
  public readonly config: StartWorkConfig;
  private readonly presentationClient: IUiPresentationClient;
  private readonly widgetRegistry: WidgetRegistry;

  constructor(options: StartWorkFeatureOptions) {
    this.config = parseStartWorkConfig(options.config);
    this.presentationClient = options.presentationClient;
    this.widgetRegistry = options.widgetRegistry;

    this.manifest = {
      ...SPEC,
      contributedWorkspaces: [
        {
          workspace_id: "workstation-main",
          route_path: "/home",
          display_name: "Workstation",
          icon_name: "🏠",
          is_authorized: true,
          renderWorkspace: () => (
            <StartWorkClientProvider client={this.presentationClient}>
              <WorkspaceHost
                workspaceId="workstation-main"
                registry={this.widgetRegistry}
                initialLayout={createHomeLayout()}
              />
            </StartWorkClientProvider>
          ),
        },
        {
          workspace_id: "workstation-research",
          route_path: "/research",
          display_name: "Research",
          icon_name: "🔬",
          is_authorized: true,
          renderWorkspace: () => (
            <WorkspaceHost
              workspaceId="workstation-research"
              registry={this.widgetRegistry}
            />
          ),
        },
        {
          workspace_id: "workstation-data",
          route_path: "/data",
          display_name: "Data",
          icon_name: "🗄️",
          is_authorized: true,
          renderWorkspace: () => (
            <WorkspaceHost
              workspaceId="workstation-data"
              registry={this.widgetRegistry}
            />
          ),
        },
      ],
    };
  }
}

export function createFeature(options: StartWorkFeatureOptions): StartWorkFeature {
  return new StartWorkFeature(options);
}
