/**
 * Scenario, checklist, and mission panel tests (FEAT-UI-31, P7-T01).
 *
 * These panels render owner evidence only: no fault is triggered here, no
 * checklist step is marked satisfied here, and a qualification appears only
 * once the owner records a pass.
 */

import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ScenarioPanel, NO_SCENARIO_EVIDENCE } from "./ScenarioPanel";
import { ChecklistPanel, NO_CHECKLIST_EVIDENCE } from "./ChecklistPanel";
import { MissionPanel, NO_MISSION_OUTCOME } from "./MissionPanel";

const SCENARIO = {
  mission_id: "mission-liquidity-gap",
  version: "1.1.0",
  difficulty: 7,
  seed: 4242,
  market_data_ref: "datasets/eurusd-2025",
  competence_tags: ["risk_control", "execution"],
  assistance_mode: "guided",
  events: [
    {
      event_id: "evt-1",
      event_type: "disconnect",
      priority: 10,
      effective_at: "2025-03-04T09:00:00Z",
      suspends_normal_transitions: true,
    },
  ],
  emergency_steps: [
    "Halt new order submission.",
    "Close all practice exposure.",
  ],
};

const CHECKLIST = {
  checklist_id: "pre-trade",
  version: "2.0.0",
  mode: "Challenge",
  steps: [
    {
      step_id: "risk_budget_confirmed",
      state: "SATISFIED",
      evidence: true,
      reason: null,
      mandatory: true,
    },
    {
      step_id: "session_hours_checked",
      state: "PENDING",
      evidence: null,
      reason: "awaiting evidence",
      mandatory: false,
    },
  ],
};

describe("ScenarioPanel", () => {
  it("states plainly when the owner supplied no scenario", () => {
    render(<ScenarioPanel />);
    expect(screen.getByText(NO_SCENARIO_EVIDENCE)).toBeInTheDocument();
  });

  it("renders the owner catalogue entry", () => {
    render(<ScenarioPanel scenario={SCENARIO} />);
    expect(
      screen.getByText("mission-liquidity-gap (1.1.0)"),
    ).toBeInTheDocument();
    expect(screen.getByText("4242")).toBeInTheDocument();
    expect(screen.getByText("risk_control, execution")).toBeInTheDocument();
  });

  it("renders the injected fault profile without triggering one", () => {
    render(<ScenarioPanel scenario={SCENARIO} />);
    expect(screen.getByText("disconnect")).toBeInTheDocument();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("renders the owner emergency steps in order", () => {
    render(<ScenarioPanel scenario={SCENARIO} />);
    const list = screen.getByRole("list");
    expect(list.textContent).toContain("Halt new order submission.");
    expect(
      (list.textContent ?? "").indexOf("Halt new order submission."),
    ).toBeLessThan((list.textContent ?? "").indexOf("Close all practice"));
  });

  it("says so when a scenario schedules no fault", () => {
    render(<ScenarioPanel scenario={{ ...SCENARIO, events: [] }} />);
    expect(
      screen.getByText("No fault event is scheduled for this scenario."),
    ).toBeInTheDocument();
  });
});

describe("ChecklistPanel", () => {
  it("states plainly when the owner supplied no checklist", () => {
    render(<ChecklistPanel />);
    expect(screen.getByText(NO_CHECKLIST_EVIDENCE)).toBeInTheDocument();
  });

  it("renders each owner-evaluated step state", () => {
    render(<ChecklistPanel checklist={CHECKLIST} />);
    const table = screen.getByRole("table");
    expect(within(table).getByText("SATISFIED")).toBeInTheDocument();
    expect(within(table).getByText("PENDING")).toBeInTheDocument();
    expect(within(table).getByText("awaiting evidence")).toBeInTheDocument();
  });

  it("offers no control that could satisfy a step locally", () => {
    render(<ChecklistPanel checklist={CHECKLIST} />);
    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.queryByRole("checkbox")).toBeNull();
  });
});

describe("MissionPanel", () => {
  it("states plainly when the owner recorded no outcome", () => {
    render(<MissionPanel />);
    expect(screen.getByText(NO_MISSION_OUTCOME)).toBeInTheDocument();
  });

  it("renders the owner completion result", () => {
    render(
      <MissionPanel
        outcome={{
          status: "PASSED",
          reason: "all mandatory steps satisfied",
          safe_stand_down: true,
          satisfied_steps: 6,
          required_steps: 6,
          qualifications: [
            {
              qualification_id: "q-1",
              label: "Practice risk control",
              href: "/workstation/training/q-1",
            },
          ],
        }}
      />,
    );
    expect(screen.getByText("PASSED")).toBeInTheDocument();
    expect(screen.getByText("6 of 6")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Practice risk control" }),
    ).toHaveAttribute("href", "/workstation/training/q-1");
  });

  it("lists no qualification until the owner records a pass", () => {
    render(
      <MissionPanel
        outcome={{
          status: "INCOMPLETE",
          reason: "two mandatory steps outstanding",
          safe_stand_down: false,
          satisfied_steps: 4,
          required_steps: 6,
          qualifications: [
            {
              qualification_id: "q-1",
              label: "Practice risk control",
              href: "/workstation/training/q-1",
            },
          ],
        }}
      />,
    );
    expect(screen.queryByRole("link")).toBeNull();
    expect(
      screen.getByText(
        "Qualifications are listed only once the owner records a pass.",
      ),
    ).toBeInTheDocument();
  });
});
