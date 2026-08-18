/**
 * Research workbench shell (FEAT-UI-28).
 *
 * Composes layout only: the persistent run header, the stage navigator, the
 * live status strip, and whichever stage panel the route selected. It holds no
 * evidence of its own and makes no Research decision.
 */

"use client";

import { useState, type ReactNode } from "react";

import type { ResearchRunDetail, ResearchStageView } from "@/clients";

import { ResearchRunHeader } from "./ResearchRunHeader";
import { ResearchRunStatus, EvidenceGate } from "./ResearchRunStatus";
import { ResearchStageNav } from "./ResearchStageNav";
import { ResearchArtifactDrawer } from "./ResearchArtifactDrawer";
import { STAGE_BY_ID } from "./stage-registry";
import { stageReason, stageState } from "./research-selectors";
import { DataQualityPanel } from "./panels/DataQualityPanel";
import { FeaturesPanel } from "./panels/FeaturesPanel";
import { IntelligencePanel } from "./panels/IntelligencePanel";
import { MarketStructurePanel } from "./panels/MarketStructurePanel";
import { MetricsPanel } from "./panels/MetricsPanel";
import { ModelingPanel } from "./panels/ModelingPanel";
import { OverviewPanel } from "./panels/OverviewPanel";
import { ProfilePanel } from "./panels/ProfilePanel";
import { ProvenancePanel } from "./panels/ProvenancePanel";
import { SeasonalityPanel } from "./panels/SeasonalityPanel";
import { StressPanel } from "./panels/StressPanel";
import { StudiesPanel } from "./panels/StudiesPanel";
import { ValidationPanel } from "./panels/ValidationPanel";
import { useStage } from "./use-research";

/** Props accepted by `ResearchWorkbench`. */
export interface ResearchWorkbenchProps {
  detail: ResearchRunDetail;
  experimentId: string;
  stage: string;
  experimentName?: string;
  onChanged?: () => void;
}

/** States in which a stage view still carries renderable evidence. */
const RENDERABLE = new Set(["completed", "partial"]);

/** Workbench layout for one run stage. */
export function ResearchWorkbench({
  detail,
  experimentId,
  stage,
  experimentName,
  onChanged,
}: ResearchWorkbenchProps): ReactNode {
  const [scenarioId, setScenarioId] = useState("");
  const definition = STAGE_BY_ID[stage];
  const view = useStage(
    detail.run_id,
    stage,
    stage === "stress" ? { scenarioId: scenarioId || undefined } : undefined
  );
  const serverState = stageState(detail, stage);
  const state = view.data?.state ?? serverState;
  const reason = view.data?.reason ?? stageReason(detail, stage);

  return (
    <div className="research-workbench">
      <ResearchRunHeader
        detail={detail}
        experimentName={experimentName}
        onChanged={onChanged}
      />
      <ResearchRunStatus detail={detail} />
      <div className="research-workbench__body">
        <ResearchStageNav
          detail={detail}
          experimentId={experimentId}
          runId={detail.run_id}
          activeStage={stage}
        />
        <main className="research-workbench__stage" aria-live="polite">
          <header className="research-workbench__stage-head">
            <h3>{definition?.label ?? stage}</h3>
            <p>{definition?.description}</p>
          </header>
          <EvidenceGate
            loading={view.loading}
            error={view.error}
            reload={view.reload}
            state={state}
            reason={reason}
            ready={
              view.data !== null &&
              (RENDERABLE.has(state) || ALWAYS_RENDERED.has(stage))
            }
            loadingLabel={`Loading ${definition?.label ?? stage} evidence…`}
          >
            {view.data ? (
              <StagePanel
                stage={stage}
                detail={detail}
                view={view.data}
                scenarioId={scenarioId}
                onScenarioChange={setScenarioId}
              />
            ) : null}
          </EvidenceGate>
        </main>
      </div>
    </div>
  );
}

/**
 * Stages that render their own explicit empty states.
 *
 * These views are meaningful even when Research produced nothing: the stress
 * and intelligence panels have to explain *why* nothing is there, and the
 * artifact and provenance views are gateway-owned.
 */
const ALWAYS_RENDERED = new Set([
  "overview",
  "artifacts",
  "provenance",
  "intelligence",
  "stress",
]);

/** Select the panel that owns one stage view. */
function StagePanel({
  stage,
  detail,
  view,
  scenarioId,
  onScenarioChange,
}: {
  stage: string;
  detail: ResearchRunDetail;
  view: ResearchStageView;
  scenarioId: string;
  onScenarioChange: (value: string) => void;
}): ReactNode {
  switch (stage) {
    case "overview":
      return <OverviewPanel detail={detail} view={view} />;
    case "data":
      return <DataQualityPanel detail={detail} view={view} />;
    case "features":
      return <FeaturesPanel detail={detail} view={view} />;
    case "validation":
      return <ValidationPanel detail={detail} view={view} />;
    case "metrics":
      return <MetricsPanel detail={detail} view={view} />;
    case "studies":
      return <StudiesPanel detail={detail} view={view} />;
    case "seasonality":
      return <SeasonalityPanel detail={detail} view={view} />;
    case "market-structure":
      return <MarketStructurePanel detail={detail} view={view} />;
    case "modeling":
      return <ModelingPanel detail={detail} view={view} />;
    case "profile":
      return <ProfilePanel detail={detail} view={view} />;
    case "intelligence":
      return <IntelligencePanel detail={detail} view={view} />;
    case "stress":
      return (
        <StressPanel
          detail={detail}
          view={view}
          scenarioId={scenarioId}
          onScenarioChange={onScenarioChange}
        />
      );
    case "artifacts":
      return <ResearchArtifactDrawer detail={detail} />;
    case "provenance":
      return <ProvenancePanel detail={detail} view={view} />;
    default:
      return (
        <p className="research-note">
          {stage} is not a registered stage view.
        </p>
      );
  }
}
