import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { StartWorkClientProvider } from "../../../features/start_work";
import type { IUiPresentationClient } from "../../../clients/ui_client";
import { ProductNewsWidget } from "../Component";
import { productNewsManifest } from "../manifest";
import { productNewsWidgetDefinition } from "../index";

function createFakeClient(
  startWork: IUiPresentationClient["startWork"]
): IUiPresentationClient & { isDevOnly: boolean } {
  const unused = async () => {
    throw new Error("unused");
  };
  return {
    isDevOnly: true,
    startWork,
    manageLayouts: unused,
    editInputs: unused,
    authorStrategies: unused,
    runResearch: unused,
    editProjects: unused,
    manageData: unused,
    operateDatabanks: unused,
    exploreResults: unused,
    composePortfolios: unused,
    editCode: unused,
    monitorWork: unused,
    administerSystem: unused,
    operateTrading: unused,
    ensureAccess: unused,
    extendViews: unused,
  };
}

const WIDGET_PROPS = {
  instance: {
    instance_id: "inst-news-test",
    widget_type: "product_news",
    workspace_id: "workstation-main",
    configuration_version: 1,
    state_version: 1,
    schema_version: 1,
  },
  configuration: {},
  state: {},
  onStateChange: () => undefined,
  onConfigChange: () => undefined,
} as const;

function renderNews(client: IUiPresentationClient) {
  return render(
    <StartWorkClientProvider client={client}>
      <ProductNewsWidget {...WIDGET_PROPS} />
    </StartWorkClientProvider>
  );
}

describe("FEAT-UI-START_WORK product news widget (FR-UI-SHOW_PRODUCT_NEWS, FR-UI-DISTINGUISH_STATE)", () => {
  afterEach(() => {
    cleanup();
  });

  it("is owned by FEAT-UI-START_WORK with a registry-valid definition", () => {
    expect(productNewsManifest.owning_feature).toBe("FEAT-UI-START_WORK");
    expect(productNewsWidgetDefinition.descriptor.widget_type).toBe("product_news");
    expect(typeof productNewsWidgetDefinition.component).toBe("function");
  });

  it("renders news items separately from workspace state and labels mock data non-authoritative", async () => {
    const client = createFakeClient(async () => ({
      outcome: "SUCCESS" as const,
      request_id: "req-news-test",
      result_version: 1,
      news: [
        {
          notification_id: "notif-1",
          title: "Release 0.1 Notes",
          message: "Mock release notes body.",
          severity: "info" as const,
          timestamp_iso: "2026-08-25T00:00:00.000Z",
          schema_version: 1,
        },
      ],
      schema_version: 1,
    }));
    renderNews(client);

    expect(await screen.findByTestId("product-news-items")).toBeDefined();
    expect(screen.getByText("Release 0.1 Notes")).toBeDefined();
    // News lives in its own dedicated widget region, not in workspace state.
    expect(screen.getByTestId("product-news-widget")).toBeDefined();
    expect(screen.getByTestId("product-news-mock-label").textContent).toContain("MOCK DATA");
  });

  it("renders explicit visible severity text, symbols, and accessible labels (FR-UI-DISTINGUISH_STATE)", async () => {
    const client = createFakeClient(async () => ({
      outcome: "SUCCESS" as const,
      request_id: "req-news-multi",
      result_version: 1,
      news: [
        {
          notification_id: "notif-info",
          title: "Maintenance Notice",
          message: "Scheduled maintenance tonight.",
          severity: "info" as const,
          timestamp_iso: "2026-08-26T00:00:00.000Z",
          schema_version: 1,
        },
        {
          notification_id: "notif-warn",
          title: "High Volatility",
          message: "CPI data release at 13:30 UTC.",
          severity: "warning" as const,
          timestamp_iso: "2026-08-26T01:00:00.000Z",
          schema_version: 1,
        },
        {
          notification_id: "notif-err",
          title: "Connector Interruption",
          message: "Primary feed disconnected.",
          severity: "error" as const,
          timestamp_iso: "2026-08-26T02:00:00.000Z",
          schema_version: 1,
        },
      ],
      schema_version: 1,
    }));
    renderNews(client);

    const infoBadge = await screen.findByTestId("product-news-severity-notif-info");
    expect(infoBadge).toHaveTextContent("[i] INFO");
    expect(infoBadge).toHaveAttribute("aria-label", "Severity: info");

    const warnBadge = screen.getByTestId("product-news-severity-notif-warn");
    expect(warnBadge).toHaveTextContent("[!] WARNING");
    expect(warnBadge).toHaveAttribute("aria-label", "Severity: warning");

    const errBadge = screen.getByTestId("product-news-severity-notif-err");
    expect(errBadge).toHaveTextContent("[x] ERROR");
    expect(errBadge).toHaveAttribute("aria-label", "Severity: error");
  });

  it("renders a non-blocking unavailable state when news fetch fails", async () => {
    const client = createFakeClient(async () => {
      throw new Error("offline");
    });
    renderNews(client);

    const status = await screen.findByTestId("product-news-unavailable", {}, { timeout: 2000 });
    expect(status.textContent).toContain("Work is not affected.");
  });

  it("renders an explicit empty state when no news exists", async () => {
    const client = createFakeClient(async () => ({
      outcome: "SUCCESS" as const,
      request_id: "req-news-empty",
      result_version: 1,
      news: [],
      schema_version: 1,
    }));
    renderNews(client);

    expect(await screen.findByTestId("product-news-empty", {}, { timeout: 2000 })).toBeDefined();
  });
});
