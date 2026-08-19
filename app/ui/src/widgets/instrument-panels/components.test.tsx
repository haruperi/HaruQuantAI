import { render, screen } from "@testing-library/react"; import { describe, expect, it } from "vitest"; import { InstrumentPanels } from ".";
describe("InstrumentPanels", () => { it("renders unknown explicitly", () => { render(<InstrumentPanels values={[{label:"Margin", value:null, freshness:"unknown"}]} />); expect(screen.getByText("Unknown")).toBeInTheDocument(); }); });
