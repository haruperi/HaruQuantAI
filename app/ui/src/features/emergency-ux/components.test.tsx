import { render, screen } from "@testing-library/react"; import { describe, expect, it, vi } from "vitest"; import { EmergencyPanel } from ".";
describe("EmergencyPanel", () => { it("guards inactive acknowledgement", () => { render(<EmergencyPanel active={false} steps={[]} onAcknowledge={vi.fn()} />); expect(screen.getByRole("button")).toBeDisabled(); }); });
