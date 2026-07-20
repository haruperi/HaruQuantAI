export type AgenticUiAuthority =
  | "ceo_agent"
  | "internal_planner"
  | "specialist_evidence"
  | "deterministic_service"
  | "risk_governor"
  | "order_router"
  | "board"
  | "audit"

export type AccountMode =
  | "research"
  | "simulation"
  | "paper"
  | "micro-live"
  | "live"
  | "disabled"

export type DeterministicDecisionStatus =
  | "allowed"
  | "blocked"
  | "rejected"
  | "needs_approval"
  | "unknown"

export type UiActionIntent =
  | "view_only"
  | "local_ui"
  | "backend_non_trading"
  | "trading_adjacent"
  | "paper_order"
  | "live_order"
  | "live_activation"
  | "risk_policy_change"
  | "kill_switch_reset"
  | "prohibited"

export type EvidenceFirstSurface =
  | "recommendation"
  | "approval_request"
  | "rejection"
  | "risk_block"
  | "generated_strategy"
  | "backtest"
  | "portfolio_decision"
  | "live_execution"

export interface DeterministicDecisionSummary {
  status: DeterministicDecisionStatus
  policyVersion: string
  promptVersion?: string | null
  llmUsed: boolean
  toolsUsed: string[]
  allowedActions: string[]
  blockedActions: string[]
  reasons: string[]
  approvalToken?: string | null
}

export interface ExecutionSafetyState {
  accountMode: AccountMode
  boardApproved: boolean
  riskGovernorApproved: boolean
  riskGovernorApprovalToken?: string | null
  killSwitchActive: boolean
  orderRouterAvailable: boolean
  brokerHeartbeatOk: boolean
  auditLoggerAvailable: boolean
}

export interface GovernedUiAction {
  intent: UiActionIntent
  workflowId?: string | null
  requestId?: string | null
  userApprovalId?: string | null
  approvalToken?: string | null
  boardApprovalId?: string | null
  criticalIncidentApprovalId?: string | null
  userPermission?: string | null
  serverPermissionCheck?: boolean
  auditRecordIntent?: string | null
  evidenceRefs?: string[]
}

export interface GovernedUiActionEvaluation {
  allowed: boolean
  reasons: string[]
  requiredRoute: "ceo_gateway" | "order_router" | "board_room" | "read_only"
}

export interface EvidenceFirstUiRecord {
  surface: EvidenceFirstSurface
  evidenceRefs?: string[]
  sourceReports?: string[]
  deterministicReasons?: string[]
  riskThreshold?: string | number | null
  observedValue?: string | number | null
  researchHypothesisId?: string | null
  strategySpecVersion?: string | null
  strategyCodeHash?: string | null
  riskReviewId?: string | null
  performanceEvidenceRefs?: string[]
  approvalToken?: string | null
  brokerResponseId?: string | null
}

export interface EvidenceFirstUiEvaluation {
  complete: boolean
  missing: string[]
}

export const CORE_UI_ARCHITECTURE_RULES = [
  {
    id: "chat-orchestration",
    title: "Chat and Orchestration",
    authority: "ceo_agent" satisfies AgenticUiAuthority,
    rules: [
      "User-facing workflows enter through the CEO Agent.",
      "The frontend does not call specialist agents directly from chat.",
      "Specialist outputs are rendered as evidence, not final authority.",
      "Planner output is visible for transparency and cannot be edited into execution.",
    ],
  },
  {
    id: "deterministic-service",
    title: "Deterministic Services",
    authority: "deterministic_service" satisfies AgenticUiAuthority,
    rules: [
      "LLM proposals are labeled separately from deterministic decisions.",
      "Policy version, prompt version, tools used, reasons, allowed actions, and blocked actions stay visible.",
      "Malformed or unknown decisions fail closed.",
      "RiskGovernor approval tokens are distinct from CEO final memos.",
    ],
  },
  {
    id: "live-trading-safety",
    title: "Live Trading Safety",
    authority: "risk_governor" satisfies AgenticUiAuthority,
    rules: [
      "Live and paper execution actions require governed workflow approval.",
      "The UI does not send orders directly to broker bridges.",
      "Execution requests route through the Order Router.",
      "Kill switch, account mode, Board approval, and RiskGovernor token state are visible before execution.",
    ],
  },
  {
    id: "evidence-first",
    title: "Evidence First",
    authority: "audit" satisfies AgenticUiAuthority,
    rules: [
      "Recommendations, approvals, rejections, and risk blocks show evidence references.",
      "Approval requests show source reports.",
      "Rejections show deterministic reasons.",
      "Risk blocks show the relevant threshold and observed value.",
      "Generated strategies link to their research hypothesis.",
      "Backtests link to strategy spec version and code hash.",
      "Portfolio decisions link to risk review and performance evidence.",
      "Execution records link to approval token and broker response.",
    ],
  },
] as const

const EXECUTION_INTENTS: ReadonlySet<UiActionIntent> = new Set([
  "paper_order",
  "live_order",
  "live_activation",
  "risk_policy_change",
  "kill_switch_reset",
])

export function isExecutionIntent(intent: UiActionIntent): boolean {
  return EXECUTION_INTENTS.has(intent)
}

export function evaluateGovernedUiAction(
  action: GovernedUiAction,
  safety: ExecutionSafetyState,
): GovernedUiActionEvaluation {
  if (action.intent === "view_only" || action.intent === "local_ui") {
    return { allowed: true, reasons: [], requiredRoute: "read_only" }
  }

  if (action.intent === "prohibited") {
    return {
      allowed: false,
      reasons: ["This action is prohibited from the UI."],
      requiredRoute: "ceo_gateway",
    }
  }

  const reasons: string[] = []

  if (!action.requestId) {
    reasons.push("Missing request ID.")
  }
  if (!action.workflowId) {
    reasons.push("Missing workflow ID.")
  }
  if (!action.evidenceRefs?.length) {
    reasons.push("Missing evidence references.")
  }
  if (!action.serverPermissionCheck || !action.userPermission) {
    reasons.push("Missing server-side permission check.")
  }
  if (!action.userApprovalId && action.intent !== "backend_non_trading" && action.intent !== "trading_adjacent") {
    reasons.push("Missing explicit user approval.")
  }
  if (!action.auditRecordIntent) {
    reasons.push("Missing audit record intent.")
  }

  if (isExecutionIntent(action.intent) || action.intent === "trading_adjacent") {
    if (safety.killSwitchActive) {
      reasons.push("Kill switch is active.")
    }
    if (!safety.riskGovernorApproved || !safety.riskGovernorApprovalToken) {
      reasons.push("Missing RiskGovernor approval token.")
    }
    if (!safety.orderRouterAvailable) {
      reasons.push("Order Router is unavailable.")
    }
    if (!safety.auditLoggerAvailable) {
      reasons.push("Audit logger is unavailable.")
    }
  }

  if (action.intent === "live_order" || action.intent === "live_activation") {
    if (safety.accountMode !== "live" && safety.accountMode !== "micro-live") {
      reasons.push(`Account mode is ${safety.accountMode}, not live-enabled.`)
    }
    if (!safety.boardApproved || !action.boardApprovalId) {
      reasons.push("Missing Board approval.")
    }
    if (!safety.brokerHeartbeatOk) {
      reasons.push("Broker heartbeat is not healthy.")
    }
  }

  if (action.intent === "kill_switch_reset" && !action.criticalIncidentApprovalId) {
    reasons.push("Missing critical-incident recovery approval.")
  }

  return {
    allowed: reasons.length === 0,
    reasons,
    requiredRoute: isExecutionIntent(action.intent) || action.intent === "trading_adjacent"
      ? "order_router"
      : "ceo_gateway",
  }
}

export function evaluateEvidenceFirstUi(record: EvidenceFirstUiRecord): EvidenceFirstUiEvaluation {
  const missing: string[] = []

  if (!record.evidenceRefs?.length) {
    missing.push("evidence references")
  }

  if (record.surface === "approval_request" && !record.sourceReports?.length) {
    missing.push("source reports")
  }
  if (record.surface === "rejection" && !record.deterministicReasons?.length) {
    missing.push("deterministic reasons")
  }
  if (record.surface === "risk_block") {
    if (record.riskThreshold === undefined || record.riskThreshold === null || record.riskThreshold === "") {
      missing.push("risk threshold")
    }
    if (record.observedValue === undefined || record.observedValue === null || record.observedValue === "") {
      missing.push("observed value")
    }
  }
  if (record.surface === "generated_strategy" && !record.researchHypothesisId) {
    missing.push("research hypothesis")
  }
  if (record.surface === "backtest") {
    if (!record.strategySpecVersion) missing.push("strategy spec version")
    if (!record.strategyCodeHash) missing.push("strategy code hash")
  }
  if (record.surface === "portfolio_decision") {
    if (!record.riskReviewId) missing.push("risk review")
    if (!record.performanceEvidenceRefs?.length) missing.push("performance evidence")
  }
  if (record.surface === "live_execution") {
    if (!record.approvalToken) missing.push("approval token")
    if (!record.brokerResponseId) missing.push("broker response")
  }

  return {
    complete: missing.length === 0,
    missing,
  }
}
