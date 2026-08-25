/**
 * Unit tests for FEAT-UI-ADMINISTER_SYSTEM feature container and provider.
 */

import React from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  SPEC,
  AdministerSystemClientProvider,
  createFeature,
  useAdministerSystemClient,
} from "../index";
import type { IUiPresentationClient } from "../../../clients/ui_client";

const dummyClient: IUiPresentationClient = {
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
  administerSystem: async () => ({
    outcome: "SUCCESS",
    request_id: "req-test",
    result_version: 1,
    preferences: {
      theme: "dark",
      density: "comfortable",
      font_scale: "1",
      locale: "en-US",
      schema_version: 1,
    },
    accessibility: {
      high_contrast: false,
      reduced_motion: false,
      screen_reader_optimized: false,
      schema_version: 1,
    },
    administration: null,
    schema_version: 1,
  }),
  operateTrading: async () => { throw new Error("unused"); },
  ensureAccess: async () => { throw new Error("unused"); },
  extendViews: async () => { throw new Error("unused"); },
};

const TestConsumer: React.FC = () => {
  const client = useAdministerSystemClient();
  return <div data-testid="consumer-status">{typeof client.administerSystem === "function" ? "ready" : "not-ready"}</div>;
};

describe("FEAT-UI-ADMINISTER_SYSTEM feature module", () => {
  it("declares the correct feature manifest", () => {
    expect(SPEC.featureId).toBe("FEAT-UI-ADMINISTER_SYSTEM");
    expect(SPEC.name).toBe("Administer System");
    expect(SPEC.providesCapabilities).toEqual(["ui.administer-system@1"]);
  });

  it("provides client via AdministerSystemClientProvider", () => {
    render(
      <AdministerSystemClientProvider client={dummyClient}>
        <TestConsumer />
      </AdministerSystemClientProvider>
    );
    expect(screen.getByTestId("consumer-status").textContent).toBe("ready");
  });

  it("throws when useAdministerSystemClient is called outside provider", () => {
    expect(() => render(<TestConsumer />)).toThrow(
      "useAdministerSystemClient must be used within an AdministerSystemClientProvider"
    );
  });

  it("creates feature instance with createFeature", () => {
    const feature = createFeature({ presentationClient: dummyClient });
    expect(feature.manifest.featureId).toBe("FEAT-UI-ADMINISTER_SYSTEM");
    const rendered = feature.renderClientProvider(<TestConsumer />);
    render(<>{rendered}</>);
    expect(screen.getByTestId("consumer-status").textContent).toBe("ready");
  });
});
