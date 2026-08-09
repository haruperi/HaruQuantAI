"use client";
import { AlarmModel } from "../../features/human-factors";
import { EmergencyPanel } from "../../features/emergency-ux";
import { InstrumentPanels } from "../../features/instrument-panels";
import { PlanningPanels } from "../../features/planning";
import { TrainingPanel } from "../../features/training-ux";
import { WorkflowStages, type WorkflowStage } from "../../features/workflow-pages";

export function WorkstationView({ stage = "pre-market" }: { stage?: WorkflowStage }): React.JSX.Element {
  return <main className="workstation-shell"><header><p className="eyebrow">Operational workstation</p><h1>{stage.replace("-", " ")}</h1><span className="freshness">Evidence status: current</span></header><WorkflowStages active={stage} allowed={["pre-market","trade-planning","execution","management","post-market"]}/><InstrumentPanels values={[{label:"Market",value:"Connected",freshness:"current"},{label:"Portfolio",value:"Unknown",freshness:"unknown"},{label:"Trade",value:"Standby",freshness:"current"}]}/><PlanningPanels mode={stage} warnings={[]}/><AlarmModel alarms={[]}/><EmergencyPanel active={false} steps={[]} onAcknowledge={() => undefined}/><TrainingPanel qualification={{status:"unknown",curriculumVersion:null,remediation:[]}} /></main>;
}
