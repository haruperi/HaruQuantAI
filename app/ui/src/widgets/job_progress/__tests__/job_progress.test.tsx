import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { MonitorWorkClientProvider } from "../../../features/monitor_work";
import type { IUiPresentationClient } from "../../../clients/ui_client";
import { JobProgressWidget } from "../Component";
import { jobProgressManifest } from "../manifest";
import { jobProgressWidgetDefinition } from "../index";
import {
  MOCK_MONITOR_WORK_SUCCESS,
  MOCK_MONITOR_WORK_FAILURE,
} from "../../../mocks/fixtures";

function createFakeClient(
  overrides: Partial<IUiPresentationClient> = {}
): IUiPresentationClient & { isDevOnly: boolean } {
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
    monitorWork: async () => MOCK_MONITOR_WORK_SUCCESS,
    administerSystem: async () => { throw new Error("unused"); },
    operateTrading: async () => { throw new Error("unused"); },
    ensureAccess: async () => { throw new Error("unused"); },
    extendViews: async () => { throw new Error("unused"); },
    ...overrides,
  };
}

const dummyProps = {
  instance: {
    instance_id: "inst-progress-test",
    widget_type: "job_progress",
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

describe("FEAT-UI-MONITOR_WORK job_progress widget (FR-UI-TRACK_PROGRESS, FR-UI-PRESENT_FAILURES)", () => {
  afterEach(() => {
    cleanup();
  });

  it("is owned by FEAT-UI-MONITOR_WORK with a valid widget definition", () => {
    expect(jobProgressManifest.owning_feature).toBe("FEAT-UI-MONITOR_WORK");
    expect(jobProgressWidgetDefinition.descriptor.widget_type).toBe("job_progress");
    expect(typeof jobProgressWidgetDefinition.component).toBe("function");
  });

  it("renders bounded progress, stage, message, and mock label (FR-UI-TRACK_PROGRESS)", async () => {
    const client = createFakeClient();
    render(
      <MonitorWorkClientProvider client={client}>
        <JobProgressWidget {...dummyProps} />
      </MonitorWorkClientProvider>
    );

    expect(await screen.findByTestId("job-progress-widget")).toBeInTheDocument();
    expect(await screen.findByTestId("job-progress-task-id")).toHaveTextContent("task-mock-1");
    expect(screen.getByTestId("job-progress-stage")).toHaveTextContent("Running Mock Simulation");
    expect(screen.getByTestId("job-progress-percent")).toHaveTextContent("75.5%");
    expect(screen.getByTestId("job-progress-message")).toHaveTextContent("Processing bars...");
    expect(screen.getByTestId("job-progress-mock-label")).toBeInTheDocument();
  });

  it("labels indeterminate work indeterminate without fabricating precision (R15)", async () => {
    const client = createFakeClient({
      monitorWork: async () => ({
        outcome: "SUCCESS",
        request_id: "req-indet",
        result_version: 1,
        progress: {
          task_id: "task-indet-1",
          stage_name: "Discovering Data Feeds",
          progress_percent: null,
          is_indeterminate: true,
          message: "Searching providers...",
          schema_version: 1,
        },
        notification: null,
        error: null,
        schema_version: 1,
      }),
    });

    render(
      <MonitorWorkClientProvider client={client}>
        <JobProgressWidget {...dummyProps} />
      </MonitorWorkClientProvider>
    );

    expect(await screen.findByTestId("job-progress-indeterminate")).toBeInTheDocument();
    expect(screen.getByTestId("job-progress-indeterminate")).toHaveTextContent("Progress: Indeterminate");
    expect(screen.queryByTestId("job-progress-percent")).not.toBeInTheDocument();
  });

  it("presents structured failure cards with error code, retryability, and causal reference (R16 / FR-UI-PRESENT_FAILURES)", async () => {
    const client = createFakeClient({
      monitorWork: async () => MOCK_MONITOR_WORK_FAILURE,
    });

    render(
      <MonitorWorkClientProvider client={client}>
        <JobProgressWidget {...dummyProps} />
      </MonitorWorkClientProvider>
    );

    expect(await screen.findByTestId("job-progress-failure-card")).toBeInTheDocument();
    expect(screen.getByTestId("failure-error-code")).toHaveTextContent("ERR_DATA_FETCH_TIMEOUT");
    expect(screen.getByTestId("failure-title")).toHaveTextContent("Data Fetch Timeout (Mock)");
    expect(screen.getByTestId("failure-detail")).toHaveTextContent("Historical tick feed connection timed out after 30 seconds.");
    expect(screen.getByTestId("failure-causal-ref")).toHaveTextContent("req-fetch-mock-998");
    expect(screen.getByTestId("failure-retryability")).toHaveTextContent("Retryable");
    expect(screen.getByTestId("failure-suggested-action")).toHaveTextContent("Check connectivity and retry the data sync job.");
  });

  it("handles provider failure gracefully with a non-blocking unavailable state", async () => {
    const client = createFakeClient({
      monitorWork: async () => {
        throw new Error("Network failure");
      },
    });

    render(
      <MonitorWorkClientProvider client={client}>
        <JobProgressWidget {...dummyProps} />
      </MonitorWorkClientProvider>
    );

    expect(await screen.findByTestId("job-progress-unavailable")).toBeInTheDocument();
    expect(screen.getByTestId("job-progress-unavailable")).toHaveTextContent(
      "Work monitoring provider unavailable."
    );
  });
});
