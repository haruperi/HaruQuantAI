/**
 * Component tests for the new-workspace template picker (FEAT-UI-01,
 * FR-UI-195 through FR-UI-198 in `app/ui/README.md` §4.1).
 */
import { beforeEach, describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { TemplatePicker } from "./TemplatePicker";
import { useWorkspaceStore } from "./store";
import { WORKSPACE_TEMPLATES } from "./templates";

const initialState = useWorkspaceStore.getState();

beforeEach(() => {
  useWorkspaceStore.setState(initialState, true);
  window.localStorage?.clear();
});

describe("FR-UI-195/198 template catalog rendering", () => {
  it("renders one labeled, button-operable card per registered template", () => {
    render(<TemplatePicker />);

    for (const template of WORKSPACE_TEMPLATES) {
      expect(
        screen.getByRole("button", { name: `Create workspace from the ${template.name} template` })
      ).toBeInTheDocument();
    }
    expect(screen.getByRole("heading", { name: "NEW WORKSPACE" })).toBeInTheDocument();
    expect(screen.getByText("Select a template or begin from scratch")).toBeInTheDocument();
  });

  it("shows the owner-requested template set", () => {
    render(<TemplatePicker />);
    const labels = WORKSPACE_TEMPLATES.map((t) => t.name);
    expect(labels).toEqual(["Blank", "HaruQuant", "Chart + Ladder", "MultiCharts + Ladder", "Options", "Charts"]);
  });
});

describe("FR-UI-196 applying a content template from the picker", () => {
  it("seeds and renames the active pending workspace when a card is clicked", () => {
    useWorkspaceStore.getState().addWorkspace();
    render(<TemplatePicker />);

    fireEvent.click(screen.getByRole("button", { name: "Create workspace from the Options template" }));

    const ws = useWorkspaceStore.getState().workspaces.find((w) => w.name === "Options")!;
    expect(ws.widgets.map((w) => w.type)).toEqual(["markets", "optionsGrid", "positions"]);
    expect(ws.widgets.find((w) => w.type === "optionsGrid")).toMatchObject({ symbol: "EURUSD", title: "EURUSD Options" });
    expect(ws.templateChoicePending).toBeFalsy();
  });
});

describe("FR-UI-197 applying Blank from the picker", () => {
  it("empties the workspace and keeps the deterministic name", () => {
    useWorkspaceStore.getState().addWorkspace();
    render(<TemplatePicker />);

    fireEvent.click(screen.getByRole("button", { name: "Create workspace from the Blank template" }));

    const state = useWorkspaceStore.getState();
    const ws = state.workspaces.find((w) => w.id === state.activeWorkspaceId)!;
    expect(ws.name).toBe("New Workspace-2");
    expect(ws.widgets).toEqual([]);
    expect(ws.templateChoicePending).toBeFalsy();
  });
});
