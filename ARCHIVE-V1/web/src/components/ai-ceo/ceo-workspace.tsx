"use client"

import * as React from "react"
import Link from "next/link"
import {
  AlertTriangle,
  BadgeCheck,
  Blocks,
  BrainCircuit,
  CircleDollarSign,
  ClipboardCheck,
  Copy,
  FileText,
  GitBranch,
  History,
  LinkIcon,
  LockKeyhole,
  MessageSquareText,
  MoreVertical,
  PackageOpen,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from "lucide-react"

import { ChatInput } from "@/components/ai-chat/ChatInput"
import { MessageList } from "@/components/ai-chat/MessageList"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { useChatWidgetStore, type ChatMessage } from "@/stores/chatWidgetStore"

type DetailValue = string | number | boolean | null | undefined

const departmentLinks = [
  { href: "/agents", label: "Agents" },
  { href: "/research", label: "Research" },
  { href: "/strategy-lab", label: "Strategy Lab" },
  { href: "/backtests", label: "Backtests" },
  { href: "/risk-center", label: "Risk Center" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/execution", label: "Execution" },
  { href: "/board-room", label: "Board Room" },
  { href: "/audit", label: "Audit" },
  { href: "/costs", label: "Costs" },
]

function latestAssistantMessage(messages: ChatMessage[]): ChatMessage | undefined {
  return [...messages].reverse().find((message) => message.role === "assistant")
}

function toDisplayText(value: unknown): string {
  if (value === null || value === undefined) {
    return "Not reported"
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value)
  }
  return JSON.stringify(value, null, 2)
}

function detailFromRecord(record: Record<string, unknown> | undefined, keys: string[]): DetailValue {
  if (!record) {
    return undefined
  }
  for (const key of keys) {
    const value = record[key]
    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean" || value === null) {
      return value
    }
  }
  return undefined
}

function listFromUnknown(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value
    .map((item) => {
      if (typeof item === "string") {
        return item
      }
      if (item && typeof item === "object") {
        const record = item as Record<string, unknown>
        return String(record.title ?? record.name ?? record.id ?? record.summary ?? JSON.stringify(item))
      }
      return String(item)
    })
    .filter(Boolean)
}

function valueLine(label: string, value: unknown): string {
  return `- ${label}: ${toDisplayText(value as DetailValue)}`
}

function sectionList(title: string, items: string[], empty: string): string {
  return [`## ${title}`, ...(items.length ? items.map((item) => `- ${item}`) : [`- ${empty}`])].join("\n")
}

function plannerPanelData(planner?: Record<string, unknown>) {
  const allowedAgents = plannerAgents(planner)
  return {
    planId: detailFromRecord(planner, ["plan_id", "conversation_plan_id", "id"]),
    riskLevel: detailFromRecord(planner, ["risk_level", "risk"]),
    clarification: detailFromRecord(planner, ["clarification_required", "needs_clarification"]),
    departments: uniqueItems([
      ...listFromUnknown(planner?.departments ?? planner?.selected_departments),
      ...allowedAgents.map(departmentFromAgent),
    ]),
    specialists: uniqueItems([
      ...listFromUnknown(planner?.specialists ?? planner?.selected_specialist_agents ?? planner?.agents),
      ...allowedAgents
        .filter((agent) => !["ceo", "audit"].includes(agent) && !agent.includes("orchestrator"))
        .map(labelFromAgent),
    ]),
    expectedOutputs: listFromUnknown(planner?.expected_outputs),
    evidenceRequirements: listFromUnknown(planner?.evidence_requirements),
    missingInputs: listFromUnknown(planner?.missing_inputs),
    tools: listFromUnknown(planner?.tools ?? planner?.planned_tools),
  }
}

function evidenceItems(message?: ChatMessage): string[] {
  const specialistEvidence = (message?.specialistArtifacts ?? []).flatMap((artifact) => {
    const sources = artifact.sources?.length ? artifact.sources : ["No source reference reported"]
    return sources.map((source) => `${artifact.agent_name}: ${source}`)
  })
  const memoEvidence = listFromUnknown(message?.ceoMemo?.evidence_refs).map((ref) => `CEO memo: ${ref}`)
  const plannerEvidence = listFromUnknown(message?.planner?.evidence_requirements).map((ref) => `Planner required: ${ref}`)
  return uniqueItems([...memoEvidence, ...plannerEvidence, ...specialistEvidence])
}

function artifactItems(message?: ChatMessage): string[] {
  const specialistArtifacts = (message?.specialistArtifacts ?? []).map((artifact) => `${artifact.agent_name}: ${artifact.summary}`)
  const strategyId = message?.strategyCreator?.artifact?.saved_strategy?.id
  const strategyPath = message?.strategyCreator?.artifact?.saved_strategy?.active_file_path
  return [
    ...specialistArtifacts,
    strategyId ? `Saved strategy: ${strategyId}` : null,
    strategyPath ? `Strategy file: ${strategyPath}` : null,
    message?.actionDraft?.execution_receipt_id ? `Execution receipt: ${message.actionDraft.execution_receipt_id}` : null,
  ].filter((item): item is string => Boolean(item))
}

function taskItems(message?: ChatMessage): string[] {
  const planner = message?.planner
  const plannedOutputs = listFromUnknown(planner?.expected_outputs).map((output) => `produce ${output}`)
  const plannedTools = listFromUnknown(planner?.backend_tools_to_run).map((tool) => `run read-only tool ${tool}`)
  return uniqueItems([
    ...listFromUnknown(planner?.tasks ?? planner?.task_tree ?? planner?.workflow_tasks),
    ...plannedOutputs,
    ...plannedTools,
  ])
}

function workflowUsed(message?: ChatMessage): DetailValue {
  const workflowName =
    detailFromRecord(message?.planner, ["workflow_name"]) ??
    detailFromRecord(message?.ceoMemo, ["workflow_name"]) ??
    detailFromRecord(message?.audit, ["workflow_name"])
  const workflowId =
    detailFromRecord(message?.planner, ["workflow_id", "research_workflow_id", "governed_workflow_id"]) ??
    detailFromRecord(message?.ceoMemo, ["workflow_id", "research_workflow_id", "governed_workflow_id"]) ??
    detailFromRecord(message?.audit, ["workflow_id", "research_workflow_id", "governed_workflow_id"]) ??
    message?.actionDraft?.governed_workflow_id

  if (workflowName && workflowId && workflowName !== workflowId) {
    return `${workflowName} (${workflowId})`
  }
  return workflowName ?? workflowId
}

function copyableRightPanelMarkdown(message?: ChatMessage): string {
  const planner = plannerPanelData(message?.planner)
  const decision = message?.deterministicDecision
  const audit = message?.audit
  const finalMemo = String(detailFromRecord(message?.ceoMemo, ["summary", "answer", "final_memo", "memo"]) ?? message?.content ?? "No final memo reported.")
  const tools = message?.toolCalls?.length ? message.toolCalls : listFromUnknown(audit?.tools_used)
  const blocked = [
    ...listFromUnknown(decision?.blocked_actions),
    ...listFromUnknown(decision?.reasons),
  ]

  return [
    "# AI CEO Right Panel",
    "",
    "## Final CEO Memo",
    finalMemo,
    "",
    "## Planner Trace",
    [
      valueLine("Plan ID", planner.planId),
      valueLine("Risk Level", planner.riskLevel),
      valueLine("Clarification", planner.clarification),
    ].join("\n"),
    "",
    sectionList("Planner-selected Departments", planner.departments, "No planner department selection reported yet."),
    "",
    sectionList("Specialists Routed Through CEO", planner.specialists, "No specialist evidence selected yet."),
    "",
    sectionList("Expected Outputs", planner.expectedOutputs, "No expected outputs reported."),
    "",
    sectionList("Evidence Requirements", planner.evidenceRequirements, "No evidence requirements reported."),
    "",
    sectionList("Missing Inputs", planner.missingInputs, "No missing inputs reported."),
    "",
    sectionList("Planned Tools", planner.tools, "No planned backend tools reported."),
    "",
    sectionList("Active Task Tree", taskItems(message), "No active workflow tasks reported for this conversation yet."),
    "",
    sectionList("Evidence References", evidenceItems(message), "Evidence from specialist services will appear here."),
    "",
    sectionList("Artifact Links", artifactItems(message), "Generated artifacts and immutable links will appear here."),
    "",
    "## Approval Request",
    message?.actionDraft
      ? [
          valueLine("Draft ID", message.actionDraft.draft_id),
          valueLine("Type", message.actionDraft.draft_type),
          valueLine("Status", message.actionDraft.status),
          valueLine("Risk Check", message.actionDraft.risk_precheck_status),
          valueLine("Workflow", message.actionDraft.governed_workflow_id),
          valueLine("Approval", message.actionDraft.approval_id),
        ].join("\n")
      : "Governed approval cards will appear here when the CEO drafts an action.",
    "",
    "## Deterministic Decision",
    [
      valueLine("Status", detailFromRecord(decision, ["status", "decision", "result"])),
      valueLine("Policy", detailFromRecord(decision, ["policy_version"]) ?? detailFromRecord(audit, ["policy_version"])),
      valueLine("Prompt", detailFromRecord(decision, ["prompt_version"]) ?? detailFromRecord(audit, ["prompt_version"])),
      valueLine("LLM Used", detailFromRecord(decision, ["llm_used"]) ?? detailFromRecord(audit, ["llm_used"])),
      valueLine("Approval", detailFromRecord(decision, ["approval_token", "risk_governor_token"])),
    ].join("\n"),
    "",
    sectionList("Allowed Actions", listFromUnknown(decision?.allowed_actions), "No allowed actions reported."),
    "",
    sectionList("Blocked Actions and Reasons", blocked, "No policy or risk block is active for the latest CEO turn."),
    "",
    "## Model, Tools, Audit",
    [
      valueLine("Source", message?.generationSource),
      valueLine("Provider", message?.providerName),
      valueLine("Model", message?.model),
      valueLine("Request ID", message?.requestId),
      valueLine("Trace ID", detailFromRecord(audit, ["trace_id", "conversation_trace_id"])),
      valueLine("Policy", detailFromRecord(audit, ["policy_version"])),
      valueLine("Prompt", detailFromRecord(audit, ["prompt_version"])),
    ].join("\n"),
    "",
    sectionList("Tools Used", tools, "No tools reported for the latest CEO turn."),
    "",
    "## Workflow Cost",
    [
      valueLine("Workflow Used", workflowUsed(message)),
      valueLine("Latency", message?.telemetry?.latency_ms != null ? `${message.telemetry.latency_ms} ms` : undefined),
      valueLine("Prompt Tokens", message?.telemetry?.prompt_tokens),
      valueLine("Completion Tokens", message?.telemetry?.completion_tokens),
      valueLine("Thought Tokens", message?.telemetry?.thought_tokens),
      valueLine("Tokens", message?.telemetry?.total_tokens),
      valueLine("Token Source", message?.telemetry?.token_source),
      valueLine("Cost", message?.telemetry?.cost_usd != null ? `$${message.telemetry.cost_usd}` : undefined),
      valueLine("Estimate", message?.costPolicy?.estimated_cost_usd != null ? `$${message.costPolicy.estimated_cost_usd}` : undefined),
      valueLine("Pricing Source", message?.costPolicy?.pricing_source),
      valueLine("Workflow Budget", message?.costPolicy?.workflow_budget_usd != null ? `$${message.costPolicy.workflow_budget_usd}` : undefined),
      valueLine("Budget OK", message?.costPolicy?.within_workflow_budget),
    ].join("\n"),
    "",
    "## Clarification and Resume",
    [
      valueLine("Clarification", message?.clarificationRequired),
      valueLine("Active Topic", message?.activeTopic),
      valueLine("Plan ID", message?.conversationPlanId),
    ].join("\n"),
  ].join("\n")
}

function uniqueItems(items: Array<string | null | undefined>): string[] {
  return Array.from(new Set(items.filter((item): item is string => Boolean(item?.trim()))))
}

function labelFromAgent(agent: string): string {
  return agent
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function departmentFromAgent(agent: string): string | null {
  if (agent.includes("research") || agent.includes("market_intelligence") || agent.includes("technical_analyst") || agent.includes("strategy_scout") || agent.includes("news_sentiment") || agent.includes("macro_fundamental") || agent.includes("cross_asset") || agent.includes("seasonality")) return "Research Department"
  if (agent.includes("strategy_")) return "Strategy Lab"
  if (agent.includes("simulation") || agent.includes("backtest") || agent.includes("optimization") || agent.includes("robustness") || agent.includes("statistical")) return "Simulation Department"
  if (agent.includes("risk")) return "Risk Department"
  if (agent.includes("portfolio") || agent.includes("allocation") || agent.includes("performance") || agent.includes("cost")) return "Portfolio Department"
  if (agent.includes("execution") || agent.includes("paper_execution") || agent.includes("live_execution")) return "Execution Department"
  if (agent.includes("audit")) return "Audit Department"
  if (agent === "ceo") return "Executive Department"
  return null
}

function plannerAgents(planner?: Record<string, unknown>): string[] {
  return listFromUnknown(planner?.allowed_agents)
}

function Panel({
  title,
  icon: Icon,
  children,
  action,
}: {
  title: string
  icon: React.ComponentType<{ className?: string }>
  children: React.ReactNode
  action?: React.ReactNode
}) {
  return (
    <section className="rounded border bg-background">
      <div className="flex items-center justify-between gap-3 border-b px-4 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <Icon className="h-4 w-4 text-muted-foreground" />
          <h2 className="truncate text-sm font-semibold">{title}</h2>
        </div>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </section>
  )
}

function EmptyState({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-muted-foreground">{children}</p>
}

function DetailList({ items }: { items: Array<{ label: string; value: DetailValue }> }) {
  return (
    <dl className="space-y-2 text-sm">
      {items.map((item) => (
        <div key={item.label} className="grid grid-cols-[8rem_minmax(0,1fr)] gap-3">
          <dt className="text-muted-foreground">{item.label}</dt>
          <dd className="min-w-0 break-words font-medium">{toDisplayText(item.value)}</dd>
        </div>
      ))}
    </dl>
  )
}

function TextList({ items, empty }: { items: string[]; empty: string }) {
  if (items.length === 0) {
    return <EmptyState>{empty}</EmptyState>
  }
  return (
    <ul className="space-y-2 text-sm text-muted-foreground">
      {items.map((item, index) => (
        <li key={`${item}_${index}`} className="flex gap-2">
          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-600" />
          <span className="min-w-0 break-words">{item}</span>
        </li>
      ))}
    </ul>
  )
}

function ConversationRail({
  activeThreadId,
  threadSearch,
  showArchivedThreads,
  threads,
  isManagingThreads,
  isStreaming,
  onCreateThread,
  onSelectThread,
  onThreadSearchChange,
  onToggleArchivedThreads,
  onRenameThread,
  onExportThread,
  onArchiveThread,
  onRestoreThread,
  onDeleteThread,
}: Pick<
  ReturnType<typeof useChatWidgetStore>,
  | "threadSearch"
  | "showArchivedThreads"
  | "threads"
  | "isManagingThreads"
  | "isStreaming"
  | "createNewThread"
  | "selectThread"
  | "setThreadSearch"
  | "toggleArchivedThreads"
  | "renameThread"
  | "exportThread"
  | "archiveThread"
  | "restoreThread"
  | "deleteThread"
> & {
  activeThreadId: string | null
  onCreateThread: () => void
  onSelectThread: (threadId: string) => void
  onThreadSearchChange: (value: string) => void
  onToggleArchivedThreads: () => void
  onRenameThread: (threadId: string, title: string) => void
  onExportThread: (threadId: string) => void
  onArchiveThread: (threadId: string) => void
  onRestoreThread: (threadId: string) => void
  onDeleteThread: (threadId: string) => void
}) {
  function handleRename(threadId: string, currentTitle: string) {
    const nextTitle = window.prompt("Rename conversation", currentTitle)
    if (nextTitle?.trim()) {
      onRenameThread(threadId, nextTitle.trim())
    }
  }

  return (
    <aside className="flex min-w-0 min-h-0 flex-col overflow-hidden rounded border bg-background">
      <div className="border-b p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="text-sm font-semibold">CEO Conversations</p>
            <p className="text-xs text-muted-foreground">Same threads as the quick panel.</p>
          </div>
          <Button size="sm" className="shrink-0" onClick={onCreateThread} disabled={isManagingThreads || isStreaming}>
            New
          </Button>
        </div>
        <input
          value={threadSearch}
          onChange={(event) => onThreadSearchChange(event.target.value)}
          placeholder="Search conversations"
          className="mt-3 h-9 w-full rounded border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onToggleArchivedThreads}
          disabled={isManagingThreads || isStreaming}
          className="mt-2 w-full justify-start"
        >
          {showArchivedThreads ? "Hide archived" : "Show archived"}
        </Button>
      </div>
      <ScrollArea className="min-h-0 flex-1">
        <div className="min-w-0 space-y-2 p-3">
          {threads.map((thread) => (
            <div
              key={thread.threadId}
              className={cn(
                "group grid min-w-0 grid-cols-[minmax(0,1fr)_2rem] items-center overflow-hidden rounded border",
                thread.threadId === activeThreadId ? "border-primary bg-muted" : "hover:bg-muted/50",
              )}
            >
              <button
                type="button"
                onClick={() => onSelectThread(thread.threadId)}
                className="block min-w-0 overflow-hidden rounded-l px-3 py-2 text-left text-sm"
              >
                <span className="block min-w-0 truncate font-medium">{thread.title}</span>
                <span className="mt-1 block min-w-0 truncate text-xs text-muted-foreground">
                  {thread.pageType ?? "generic"} | {new Date(thread.updatedAt).toLocaleString()}
                </span>
              </button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label={`Conversation actions for ${thread.title}`}
                    disabled={isManagingThreads || isStreaming}
                    className="h-8 w-8 shrink-0 rounded-none rounded-r bg-background/80 opacity-100 hover:bg-muted"
                  >
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => handleRename(thread.threadId, thread.title)}>
                    Rename
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onExportThread(thread.threadId)}>
                    Export
                  </DropdownMenuItem>
                  {thread.status === "archived" ? (
                    <DropdownMenuItem onClick={() => onRestoreThread(thread.threadId)}>
                      Restore
                    </DropdownMenuItem>
                  ) : (
                    <DropdownMenuItem onClick={() => onArchiveThread(thread.threadId)}>
                      Archive
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem
                    onClick={() => onDeleteThread(thread.threadId)}
                    className="text-destructive focus:text-destructive"
                  >
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          ))}
          {threads.length === 0 ? <EmptyState>No conversations yet.</EmptyState> : null}
        </div>
      </ScrollArea>
    </aside>
  )
}

function FinalMemoPanel({ message, onCopy }: { message?: ChatMessage; onCopy: () => void }) {
  const memo = message?.ceoMemo
  const summary = detailFromRecord(memo, ["summary", "answer", "final_memo", "memo"])
  const content = summary ?? message?.content

  return (
    <Panel
      title="Final CEO Memo"
      icon={FileText}
      action={
        <Button type="button" variant="ghost" size="sm" onClick={onCopy} disabled={!content}>
          <Copy className="mr-2 h-4 w-4" />
          Copy
        </Button>
      }
    >
      {content ? (
        <div className="space-y-3">
          <p className="whitespace-pre-wrap text-sm leading-6">{String(content)}</p>
          <div className="flex flex-wrap gap-2">
            {detailFromRecord(memo, ["risk_level"]) ? <Badge variant="secondary">Risk: {String(detailFromRecord(memo, ["risk_level"]))}</Badge> : null}
            {detailFromRecord(memo, ["confidence"]) ? <Badge variant="secondary">Confidence: {String(detailFromRecord(memo, ["confidence"]))}</Badge> : null}
          </div>
        </div>
      ) : (
        <EmptyState>The next CEO response will appear here as the final memo.</EmptyState>
      )}
    </Panel>
  )
}

function PlannerPanel({ planner }: { planner?: Record<string, unknown> }) {
  const data = plannerPanelData(planner)

  return (
    <Panel title="Planner Trace" icon={GitBranch}>
      <DetailList
        items={[
          { label: "Plan ID", value: data.planId },
          { label: "Risk Level", value: data.riskLevel },
          { label: "Clarification", value: data.clarification },
        ]}
      />
      <div className="mt-4 space-y-4">
        <div>
          <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Planner-selected Departments</p>
          <TextList items={data.departments} empty="No planner department selection reported yet." />
        </div>
        <div>
          <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Specialists Routed Through CEO</p>
          <TextList items={data.specialists} empty="No specialist evidence selected yet." />
        </div>
        <div>
          <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Expected Outputs</p>
          <TextList items={data.expectedOutputs} empty="No expected outputs reported." />
        </div>
        <div>
          <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Evidence Requirements</p>
          <TextList items={data.evidenceRequirements} empty="No evidence requirements reported." />
        </div>
        <div>
          <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Missing Inputs</p>
          <TextList items={data.missingInputs} empty="No missing inputs reported." />
        </div>
        <div>
          <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Planned Tools</p>
          <TextList items={data.tools} empty="No planned backend tools reported." />
        </div>
      </div>
    </Panel>
  )
}

function EvidencePanel({ message }: { message?: ChatMessage }) {
  return (
    <Panel title="Evidence References" icon={LinkIcon}>
      <TextList items={evidenceItems(message)} empty="Evidence from specialist services will appear here. The CEO will not promote or execute without evidence refs." />
    </Panel>
  )
}

function ArtifactPanel({ message }: { message?: ChatMessage }) {
  const strategyId = message?.strategyCreator?.artifact?.saved_strategy?.id

  return (
    <Panel title="Artifact Links" icon={PackageOpen}>
      <TextList items={artifactItems(message)} empty="Generated artifacts and immutable links will appear here." />
      {strategyId ? (
        <Button variant="outline" size="sm" asChild className="mt-3">
          <Link href={`/strategies/${strategyId}`}>Open strategy</Link>
        </Button>
      ) : null}
    </Panel>
  )
}

function TaskPanel({ message }: { message?: ChatMessage }) {
  return (
    <Panel title="Active Task Tree" icon={Blocks}>
      <TextList items={taskItems(message)} empty="No active workflow tasks reported for this conversation yet." />
    </Panel>
  )
}

function DecisionPanel({ message }: { message?: ChatMessage }) {
  const decision = message?.deterministicDecision
  const audit = message?.audit
  const allowed = listFromUnknown(decision?.allowed_actions)
  const blocked = listFromUnknown(decision?.blocked_actions)
  const reasons = listFromUnknown(decision?.reasons ?? decision?.approval_reasons ?? decision?.rejection_reasons)

  return (
    <Panel title="Deterministic Decision" icon={ShieldCheck}>
      <DetailList
        items={[
          { label: "Status", value: detailFromRecord(decision, ["status", "decision", "result"]) },
          { label: "Policy", value: detailFromRecord(decision, ["policy_version"]) ?? detailFromRecord(audit, ["policy_version"]) },
          { label: "Prompt", value: detailFromRecord(decision, ["prompt_version"]) ?? detailFromRecord(audit, ["prompt_version"]) },
          { label: "LLM Used", value: detailFromRecord(decision, ["llm_used"]) ?? detailFromRecord(audit, ["llm_used"]) },
          { label: "Approval", value: detailFromRecord(decision, ["approval_token", "risk_governor_token"]) },
        ]}
      />
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div>
          <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Allowed Actions</p>
          <TextList items={allowed} empty="No allowed actions reported." />
        </div>
        <div>
          <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Blocked Actions</p>
          <TextList items={blocked} empty="No blocked actions reported." />
        </div>
      </div>
      <div className="mt-4">
        <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Reasons</p>
        <TextList items={reasons} empty="No approval or rejection reasons reported." />
      </div>
    </Panel>
  )
}

function ApprovalPanel({
  message,
  onRequestApproval,
  onPaperExecute,
}: {
  message?: ChatMessage
  onRequestApproval: (draftId: string) => void
  onPaperExecute: (draftId: string) => void
}) {
  const draft = message?.actionDraft
  const [rejectedDraftIds, setRejectedDraftIds] = React.useState<Set<string>>(() => new Set())
  const [confirmationPhrase, setConfirmationPhrase] = React.useState("")
  const [interactionLog, setInteractionLog] = React.useState<string[]>([])
  const payload = draft?.payload
  const evidenceRefs = [
    ...(message?.specialistArtifacts ?? []).flatMap((artifact) => artifact.sources ?? []),
    ...listFromUnknown(payload?.evidence_refs),
  ].filter((value, index, values) => values.indexOf(value) === index)
  const riskBlocked = draft?.risk_precheck_status === "blocked"
  const killSwitchActive = detailFromRecord(payload, ["kill_switch_active"]) === true
  const evidenceMissing = !!draft && evidenceRefs.length === 0
  const isCritical = draft?.draft_type === "order_draft" || String(payload?.mode ?? payload?.account_mode ?? "").includes("live")
  const confirmationRequired = isCritical && confirmationPhrase !== "APPROVE"
  const isLocallyRejected = !!draft && rejectedDraftIds.has(draft.draft_id)
  const approvalDisabled =
    !draft
    || !!draft.approval_id
    || draft.status !== "draft"
    || !draft.requires_human_approval
    || riskBlocked
    || killSwitchActive
    || evidenceMissing
    || confirmationRequired
    || isLocallyRejected

  return (
    <Panel title="Approval Request" icon={ClipboardCheck}>
      {draft ? (
        <div className="space-y-3 text-sm">
          <DetailList
            items={[
              { label: "Draft ID", value: draft.draft_id },
              { label: "Type", value: draft.draft_type },
              { label: "Status", value: draft.status },
              { label: "Risk Check", value: draft.risk_precheck_status },
              { label: "Workflow", value: draft.governed_workflow_id },
              { label: "Approval", value: draft.approval_id },
              { label: "Strategy", value: detailFromRecord(payload, ["strategy_id", "affected_strategy"]) },
              { label: "Portfolio", value: detailFromRecord(payload, ["portfolio_id", "affected_portfolio"]) },
              { label: "Risk Level", value: detailFromRecord(payload, ["risk_level"]) },
              { label: "Expires", value: detailFromRecord(payload, ["expires_at", "expiration_time"]) },
              { label: "Kill Switch", value: killSwitchActive ? "active" : detailFromRecord(payload, ["kill_switch_status"]) },
            ]}
          />
          <p className="rounded border bg-muted/40 p-3 text-muted-foreground">{draft.risk_precheck_notes}</p>
          <div>
            <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Evidence Before Approval</p>
            <TextList items={evidenceRefs} empty="Evidence is missing, so approval is disabled." />
          </div>
          <div>
            <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Consequences</p>
            <p className="rounded border bg-muted/40 p-3 text-muted-foreground">
              {toDisplayText(detailFromRecord(payload, ["consequences", "expected_impact", "rejection_impact"]) ?? "No consequence summary reported.")}
            </p>
          </div>
          {isCritical ? (
            <label className="block text-sm">
              <span className="text-xs font-medium uppercase text-muted-foreground">Critical approval phrase</span>
              <input
                value={confirmationPhrase}
                onChange={(event) => setConfirmationPhrase(event.target.value)}
                placeholder="Type APPROVE"
                className="mt-2 h-9 w-full rounded border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>
          ) : null}
          <TextList
            items={[
              evidenceMissing ? "Approval disabled because evidence is missing." : null,
              riskBlocked ? "Approval disabled because RiskGovernor blocked the draft." : null,
              killSwitchActive ? "Approval disabled because kill switch is active." : null,
              confirmationRequired ? "Critical approval requires the APPROVE confirmation phrase." : null,
              isLocallyRejected ? "This request was rejected in the UI review state." : null,
            ].filter((item): item is string => Boolean(item))}
            empty="Approval controls are available when policy, evidence, and confirmation checks pass."
          />
          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              onClick={() => {
                setInteractionLog((current) => [`${new Date().toISOString()} requested approval for ${draft.draft_id}`, ...current])
                onRequestApproval(draft.draft_id)
              }}
              disabled={approvalDisabled}
            >
              Request approval
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setRejectedDraftIds((current) => new Set(current).add(draft.draft_id))
                setInteractionLog((current) => [`${new Date().toISOString()} rejected ${draft.draft_id}`, ...current])
              }}
              disabled={isLocallyRejected || draft.status !== "draft"}
            >
              Reject
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onPaperExecute(draft.draft_id)}
              disabled={draft.draft_type !== "order_draft" || draft.status !== "approved" || draft.side_effect_status !== "not_executed"}
            >
              Run paper execution
            </Button>
          </div>
          <div>
            <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Approval Interaction Log</p>
            <TextList items={interactionLog} empty="Approval interactions are recorded when buttons are used." />
          </div>
        </div>
      ) : (
        <EmptyState>Governed approval cards will appear here when the CEO drafts an action.</EmptyState>
      )}
    </Panel>
  )
}

function RuntimePanel({ message }: { message?: ChatMessage }) {
  const tools = message?.toolCalls ?? []
  const auditTools = listFromUnknown(message?.audit?.tools_used)
  const shownTools = tools.length ? tools : auditTools

  return (
    <Panel title="Model, Tools, Audit" icon={BrainCircuit}>
      <DetailList
        items={[
          { label: "Source", value: message?.generationSource },
          { label: "Provider", value: message?.providerName },
          { label: "Model", value: message?.model },
          { label: "Request ID", value: message?.requestId },
          { label: "Trace ID", value: detailFromRecord(message?.audit, ["trace_id", "conversation_trace_id"]) },
          { label: "Policy", value: detailFromRecord(message?.audit, ["policy_version"]) },
          { label: "Prompt", value: detailFromRecord(message?.audit, ["prompt_version"]) },
        ]}
      />
      <div className="mt-4">
        <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Tools Used</p>
        <TextList items={shownTools} empty="No tools reported for the latest CEO turn." />
      </div>
      {message?.audit ? (
        <details className="mt-4 rounded border bg-muted/30 px-3 py-2 text-xs">
          <summary className="cursor-pointer font-medium">Audit metadata</summary>
          <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap break-words text-muted-foreground">
            {JSON.stringify(message.audit, null, 2)}
          </pre>
        </details>
      ) : null}
    </Panel>
  )
}

function CostPanel({ message }: { message?: ChatMessage }) {
  return (
    <Panel title="Workflow Cost" icon={CircleDollarSign}>
      <DetailList
        items={[
          { label: "Workflow Used", value: workflowUsed(message) },
          { label: "Latency", value: message?.telemetry?.latency_ms != null ? `${message.telemetry.latency_ms} ms` : undefined },
          { label: "Prompt Tokens", value: message?.telemetry?.prompt_tokens },
          { label: "Completion Tokens", value: message?.telemetry?.completion_tokens },
          { label: "Thought Tokens", value: message?.telemetry?.thought_tokens },
          { label: "Tokens", value: message?.telemetry?.total_tokens },
          { label: "Token Source", value: message?.telemetry?.token_source },
          { label: "Cost", value: message?.telemetry?.cost_usd != null ? `$${message.telemetry.cost_usd}` : undefined },
          { label: "Estimate", value: message?.costPolicy?.estimated_cost_usd != null ? `$${message.costPolicy.estimated_cost_usd}` : undefined },
          { label: "Pricing Source", value: message?.costPolicy?.pricing_source },
          { label: "Workflow Budget", value: message?.costPolicy?.workflow_budget_usd != null ? `$${message.costPolicy.workflow_budget_usd}` : undefined },
          { label: "Budget OK", value: message?.costPolicy?.within_workflow_budget },
        ]}
      />
    </Panel>
  )
}

function SafetyPanel({ message }: { message?: ChatMessage }) {
  const blocked = listFromUnknown(message?.deterministicDecision?.blocked_actions)
  const riskStyle = message?.responseStyle === "risk_block" || message?.responseMode === "blocked_by_policy"

  return (
    <Panel title="Why Was This Blocked?" icon={ShieldAlert}>
      {riskStyle || blocked.length > 0 ? (
        <TextList
          items={[
            ...blocked,
            ...listFromUnknown(message?.deterministicDecision?.reasons),
          ]}
          empty="Blocked response did not include detailed reasons."
        />
      ) : (
        <EmptyState>No policy or risk block is active for the latest CEO turn.</EmptyState>
      )}
    </Panel>
  )
}

export function CeoWorkspace() {
  const store = useChatWidgetStore()
  const textareaRef = React.useRef<HTMLTextAreaElement | null>(null)
  const latestMessage = React.useMemo(() => latestAssistantMessage(store.messages), [store.messages])
  const [memoCopied, setMemoCopied] = React.useState(false)

  const copyMemo = React.useCallback(async () => {
    const content = copyableRightPanelMarkdown(latestMessage)
    if (!content || typeof navigator === "undefined" || !navigator.clipboard) {
      return
    }
    await navigator.clipboard.writeText(content)
    setMemoCopied(true)
    window.setTimeout(() => setMemoCopied(false), 1400)
  }, [latestMessage])

  const activeStatus = store.activeResponseStatus ?? "CEO gateway ready."
  const pipelineProgress = store.activePipelineProgress

  return (
    <div className="flex h-[calc(100vh-8rem)] min-h-[48rem] flex-col gap-4">
      <header className="flex flex-wrap items-start justify-between gap-4 rounded border bg-background p-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-normal">AI CEO</h1>
            <Badge variant="secondary" className="gap-1">
              <BadgeCheck className="h-3.5 w-3.5" />
              CEO gateway
            </Badge>
            <Badge variant="outline" className="gap-1">
              <LockKeyhole className="h-3.5 w-3.5" />
              Governed actions only
            </Badge>
          </div>
          <p className="mt-2 max-w-4xl text-sm text-muted-foreground">
            One CEO conversation surface for planner transparency, evidence, deterministic decisions, approvals, audit, and cost.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={store.regenerateLastResponse} disabled={!store.threadId || store.isStreaming || store.messages.length === 0}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Regenerate
          </Button>
          <Button variant="outline" size="sm" onClick={() => store.exportThread(store.threadId ?? undefined)} disabled={!store.threadId}>
            <FileText className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </header>

      <div className="grid min-h-0 flex-1 gap-4 xl:grid-cols-[18rem_minmax(0,1fr)_24rem]">
        <ConversationRail
          activeThreadId={store.threadId}
          threadSearch={store.threadSearch}
          showArchivedThreads={store.showArchivedThreads}
          threads={store.threads}
          isManagingThreads={store.isManagingThreads}
          isStreaming={store.isStreaming}
          createNewThread={store.createNewThread}
          selectThread={store.selectThread}
          setThreadSearch={store.setThreadSearch}
          toggleArchivedThreads={store.toggleArchivedThreads}
          renameThread={store.renameThread}
          exportThread={store.exportThread}
          archiveThread={store.archiveThread}
          restoreThread={store.restoreThread}
          deleteThread={store.deleteThread}
          onCreateThread={() => void store.createNewThread()}
          onSelectThread={(threadId) => void store.selectThread(threadId)}
          onThreadSearchChange={store.setThreadSearch}
          onToggleArchivedThreads={store.toggleArchivedThreads}
          onRenameThread={(threadId, title) => void store.renameThread(title, threadId)}
          onExportThread={(threadId) => void store.exportThread(threadId)}
          onArchiveThread={(threadId) => void store.archiveThread(threadId)}
          onRestoreThread={(threadId) => void store.restoreThread(threadId)}
          onDeleteThread={(threadId) => void store.deleteThread(threadId)}
        />

        <section className="flex min-h-0 flex-col overflow-hidden rounded border bg-background">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <MessageSquareText className="h-4 w-4 text-muted-foreground" />
                <h2 className="truncate text-sm font-semibold">{store.threadTitle}</h2>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{activeStatus}</p>
              {pipelineProgress ? (
                <div className="mt-2 w-full max-w-md">
                  <div className="mb-1 flex items-center justify-between gap-3 text-[11px] text-muted-foreground">
                    <span className="truncate">{pipelineProgress.label}</span>
                    <span className="shrink-0 font-mono">{pipelineProgress.percent}%</span>
                  </div>
                  <Progress value={pipelineProgress.percent} className="h-1.5" />
                </div>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-2">
              {latestMessage?.responseStyle ? <Badge variant="secondary">{latestMessage.responseStyle}</Badge> : null}
              {latestMessage?.responseMode ? <Badge variant="outline">{latestMessage.responseMode}</Badge> : null}
              {memoCopied ? <Badge variant="secondary">Right panel copied</Badge> : null}
            </div>
          </div>
          <div className="min-h-0 flex-1">
            <MessageList
              messages={store.messages}
              isInitializing={!store.isHydrated || store.isInitializing || store.isRestoring}
              isOnline={store.isOnline}
              error={store.error}
              onQueueSignalProposalForReview={store.queueSignalProposalForReview}
              onRequestActionDraftApproval={store.requestActionDraftApproval}
              onExecutePaperActionDraft={store.executePaperActionDraft}
              onExecutePageAction={store.executePageAction}
              onEnablePageActionAutoApproval={store.enablePageActionAutoApproval}
              onSaveSignalProposalToWatchlist={store.saveSignalProposalToWatchlist}
              autoApprovePageActions={store.autoApprovePageActions}
              showDebug
            />
          </div>
          <ChatInput
            draft={store.draft}
            disabled={!store.isOnline || !store.isHydrated}
            isStreaming={store.isStreaming}
            textareaRef={textareaRef}
            availableTools={store.availableTools}
            selectedToolIds={store.selectedToolIds}
            onCancel={store.cancelStream}
            onDraftChange={store.setDraft}
            onToggleTool={store.toggleTool}
            onSubmit={store.submitDraft}
          />
        </section>

        <ScrollArea className="min-h-0">
          <div className="space-y-4 pr-2">
            <FinalMemoPanel message={latestMessage} onCopy={copyMemo} />
            <PlannerPanel planner={latestMessage?.planner} />
            <TaskPanel message={latestMessage} />
            <EvidencePanel message={latestMessage} />
            <ArtifactPanel message={latestMessage} />
            <ApprovalPanel
              message={latestMessage}
              onRequestApproval={(draftId) => void store.requestActionDraftApproval(draftId)}
              onPaperExecute={(draftId) => void store.executePaperActionDraft(draftId)}
            />
            <DecisionPanel message={latestMessage} />
            <SafetyPanel message={latestMessage} />
            <RuntimePanel message={latestMessage} />
            <CostPanel message={latestMessage} />
            <Panel title="Related Department Pages" icon={History}>
              <div className="grid grid-cols-2 gap-2">
                {departmentLinks.map((link) => (
                  <Button key={link.href} variant="outline" size="sm" asChild className="justify-start">
                    <Link href={link.href}>{link.label}</Link>
                  </Button>
                ))}
              </div>
            </Panel>
            <Panel title="Execution Safety Snapshot" icon={AlertTriangle}>
              <div className="space-y-2 text-sm text-muted-foreground">
                <p>Live/paper actions require server-side governance, RiskGovernor approval tokens, Order Router execution, and audit records.</p>
                <p>Kill-switch and account-mode telemetry will appear here when the execution readiness endpoint is connected.</p>
              </div>
            </Panel>
            <Panel title="Clarification and Resume" icon={Sparkles}>
              <DetailList
                items={[
                  { label: "Clarification", value: latestMessage?.clarificationRequired },
                  { label: "Active Topic", value: latestMessage?.activeTopic },
                  { label: "Plan ID", value: latestMessage?.conversationPlanId },
                ]}
              />
            </Panel>
          </div>
        </ScrollArea>
      </div>
    </div>
  )
}
