import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import {
  MonitorWorkClientProvider,
  type ActivitySnapshot,
} from "../../../features/monitor_work";
import type { IUiPresentationClient } from "../../../clients/ui_client";
import { ActivityLogWidget } from "../Component";
import { activityLogManifest } from "../manifest";
import { activityLogWidgetDefinition } from "../index";
import { MOCK_ACTIVITY_SNAPSHOT } from "../../../mocks/fixtures";

function createFakeClient(): IUiPresentationClient & { isDevOnly: boolean } {
  return {
    isDevOnly: true,
    startWork: async () => { throw new Error("unused"); },
    manageLayouts: async () => { throw new Error("unused"); },
    editInputs: async () => { throw new Error("unused"); },
    authorStrategies: async () => { throw new Error("unused"); },
    runResearch: async () => { throw new Error("unused"); },
    editProjects: async () => { throw new Error("unused"); },
    manageData: async () => { throw new Error("unused"); },
    operateDatabanks: async () => { throw new Error("unused"); },
    exploreResults: async () => { throw new Error("unused"); },
    composePortfolios: async () => { throw new Error("unused"); },
    editCode: async () => { throw new Error("unused"); },
    monitorWork: async () => { throw new Error("unused"); },
    administerSystem: async () => { throw new Error("unused"); },
    operateTrading: async () => { throw new Error("unused"); },
    ensureAccess: async () => { throw new Error("unused"); },
    extendViews: async () => { throw new Error("unused"); },
  };
}

const dummyProps = {
  instance: {
    instance_id: "inst-activity-test",
    widget_type: "activity_log",
    workspace_id: "workstation-main",
    configuration_version: 1,
    state_version: 1,
    schema_version: 1 as const,
  },
  configuration: {},
  state: {},
  onStateChange: () => undefined,
  onConfigChange: () => undefined,
};

describe("FEAT-UI-MONITOR_WORK activity_log widget (FR-UI-STREAM_ACTIVITY)", () => {
  afterEach(() => {
    cleanup();
  });

  it("is owned by FEAT-UI-MONITOR_WORK with a valid widget definition", () => {
    expect(activityLogManifest.owning_feature).toBe("FEAT-UI-MONITOR_WORK");
    expect(activityLogWidgetDefinition.descriptor.widget_type).toBe("activity_log");
    expect(typeof activityLogWidgetDefinition.component).toBe("function");
  });

  it("renders ordered activity events, sequence numbers, and mock-stage feed status (FR-UI-STREAM_ACTIVITY)", () => {
    const client = createFakeClient();
    render(
      <MonitorWorkClientProvider
        client={client}
        activitySnapshot={MOCK_ACTIVITY_SNAPSHOT}
      >
        <ActivityLogWidget {...dummyProps} />
      </MonitorWorkClientProvider>
    );

    expect(screen.getByTestId("activity-log-widget")).toBeInTheDocument();
    expect(screen.getByTestId("activity-log-feed-status")).toHaveTextContent(
      "Feed status: Awaiting live feed — de-mock stage (bounded snapshot view)"
    );

    // Verify events rendered with sequence and metadata
    expect(screen.getByTestId("activity-event-101")).toBeInTheDocument();
    expect(screen.getByTestId("event-seq-101")).toHaveTextContent("#101");
    expect(screen.getByTestId("event-type-101")).toHaveTextContent("JOB_QUEUED");
    expect(screen.getByTestId("event-msg-101")).toHaveTextContent("Job queued for execution");

    expect(screen.getByTestId("activity-event-102")).toBeInTheDocument();
    expect(screen.getByTestId("event-seq-102")).toHaveTextContent("#102");

    expect(screen.getByTestId("activity-event-105")).toBeInTheDocument();
    expect(screen.getByTestId("event-seq-105")).toHaveTextContent("#105");

    expect(screen.getByTestId("activity-log-mock-label")).toBeInTheDocument();
  });

  it("renders explicit gap marker for sequence discontinuity (R32 / FR-UI-STREAM_ACTIVITY)", () => {
    const client = createFakeClient();
    render(
      <MonitorWorkClientProvider
        client={client}
        activitySnapshot={MOCK_ACTIVITY_SNAPSHOT}
      >
        <ActivityLogWidget {...dummyProps} />
      </MonitorWorkClientProvider>
    );

    // Between seq 102 and seq 105, sequences 103 and 104 are missing
    const gapMarker = screen.getByTestId("activity-log-gap-marker");
    expect(gapMarker).toBeInTheDocument();
    expect(gapMarker).toHaveTextContent(
      "Sequence gap detected: missing sequences 103 through 104 (2 events)"
    );
  });

  it("displays staleness warning banner when snapshot is marked stale", () => {
    const client = createFakeClient();
    const staleSnapshot: ActivitySnapshot = {
      ...MOCK_ACTIVITY_SNAPSHOT,
      is_stale: true,
    };

    render(
      <MonitorWorkClientProvider
        client={client}
        activitySnapshot={staleSnapshot}
      >
        <ActivityLogWidget {...dummyProps} />
      </MonitorWorkClientProvider>
    );

    const staleBanner = screen.getByTestId("activity-log-stale-banner");
    expect(staleBanner).toBeInTheDocument();
    expect(staleBanner).toHaveTextContent(
      "Activity snapshot is stale — live reconnect pending."
    );
  });

  it("renders empty state when no activity events exist", () => {
    const client = createFakeClient();
    const emptySnapshot: ActivitySnapshot = {
      snapshot_id: "snap-empty",
      cursor: "c0",
      is_stale: false,
      generated_at_iso: "2026-08-26T00:00:00Z",
      events: [],
    };

    render(
      <MonitorWorkClientProvider
        client={client}
        activitySnapshot={emptySnapshot}
      >
        <ActivityLogWidget {...dummyProps} />
      </MonitorWorkClientProvider>
    );

    expect(screen.getByTestId("activity-log-empty")).toBeInTheDocument();
    expect(screen.getByTestId("activity-log-empty")).toHaveTextContent(
      "No activity events recorded."
    );
  });
});
