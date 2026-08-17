/**
 * Component tests for the explicit empty-workspace prompt (FEAT-UI-01,
 * FR-UI-026 and FR-UI-197 in `app/ui/README.md` §4.1).
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { WorkspaceEmptyState } from "./WorkspaceEmptyState";

describe("FR-UI-026/197 empty workspace presents an explicit prompt", () => {
  it("renders the empty-workspace heading and the sidebar next-step hint", () => {
    render(<WorkspaceEmptyState />);

    expect(screen.getByRole("heading", { name: "Your workspace is empty" })).toBeInTheDocument();
    expect(screen.getByText("Add a new widget from the menu on the left to get started!")).toBeInTheDocument();
  });
});
