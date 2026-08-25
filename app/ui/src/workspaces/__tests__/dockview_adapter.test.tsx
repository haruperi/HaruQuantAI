import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { WorkspaceHost } from "../WorkspaceHost";
import { WidgetRegistry } from "../../runtime/widget_registry";
import { systemStatusWidgetDefinition } from "../../widgets/system_status";
import { widgetCatalogueWidgetDefinition } from "../../widgets/widget_catalogue";
import { UiCompositionBridge } from "../../runtime/composition_bridge";
import { UiRuntimeProvider } from "../../runtime/context";

describe("WorkspaceHost and Dockview Integration", () => {
  it("renders workspace toolbar with add widget button and template selector", () => {
    const bridge = new UiCompositionBridge();
    const registry = new WidgetRegistry();
    registry.registerWidget(systemStatusWidgetDefinition);
    registry.registerWidget(widgetCatalogueWidgetDefinition);

    render(
      <UiRuntimeProvider bridge={bridge}>
        <WorkspaceHost workspaceId="test-ws" registry={registry} />
      </UiRuntimeProvider>
    );

    expect(screen.getByTestId("workspace-host")).toBeInTheDocument();
    expect(screen.getByText("+ Add Widget")).toBeInTheDocument();
    expect(screen.getByLabelText("Template:")).toBeInTheDocument();
    expect(screen.getByText("Clear Canvas")).toBeInTheDocument();
  });
});
