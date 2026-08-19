import { render, screen } from "@testing-library/react"; import { describe, expect, it } from "vitest"; import { WorkflowStages } from ".";
describe("WorkflowStages", () => { it("gates unavailable stages", () => { render(<WorkflowStages active="pre-market" allowed={["pre-market"]} />); expect(screen.getByRole("button", {name:"execution"})).toBeDisabled(); }); });
