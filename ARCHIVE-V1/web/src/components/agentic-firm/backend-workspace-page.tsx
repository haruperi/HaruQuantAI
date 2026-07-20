"use client"

import * as React from "react"
import {
  AlertTriangle,
  CheckCircle2,
  Database,
  FileText,
  Loader2,
  RefreshCcw,
} from "lucide-react"

import { auditClient } from "@/clients/auditClient"
import { backtestClient } from "@/clients/backtestClient"
import { boardClient } from "@/clients/boardClient"
import { costClient } from "@/clients/costClient"
import { executionClient } from "@/clients/executionClient"
import { portfolioClient } from "@/clients/portfolioClient"
import { researchClient } from "@/clients/researchClient"
import { riskClient } from "@/clients/riskClient"
import { settingsClient } from "@/clients/settingsClient"
import { strategyClient } from "@/clients/strategyClient"
import { workflowClient } from "@/clients/workflowClient"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

type PageKey =
  | "agents"
  | "research"
  | "strategy-lab"
  | "backtests"
  | "risk-center"
  | "portfolio"
  | "execution"
  | "board-room"
  | "audit"
  | "costs"
  | "settings"

type Dataset = {
  label: string
  records: Array<Record<string, unknown>>
  error?: string
}

type PageDefinition = {
  title: string
  subtitle: string
  datasets: Array<{
    label: string
    load: () => Promise<unknown>
  }>
}

const pageDefinitions: Record<PageKey, PageDefinition> = {
  agents: {
    title: "Agents",
    subtitle: "Live workflow and task data from the Agentic Firm backend.",
    datasets: [
      { label: "Workflows", load: () => workflowClient.listWorkflows() },
    ],
  },
  research: {
    title: "Research",
    subtitle: "Research reports and hypotheses from backend research tools.",
    datasets: [
      { label: "Reports", load: () => researchClient.listReports() },
      { label: "Hypotheses", load: () => researchClient.listHypotheses() },
    ],
  },
  "strategy-lab": {
    title: "Strategy Lab",
    subtitle: "Strategy registry data from backend strategy tools.",
    datasets: [
      { label: "Strategies", load: () => strategyClient.listStrategies() },
    ],
  },
  backtests: {
    title: "Backtests",
    subtitle: "Backtest runs and packages from backend simulation tools.",
    datasets: [
      { label: "Backtests", load: () => backtestClient.listBacktests() },
    ],
  },
  "risk-center": {
    title: "Risk Center",
    subtitle: "Risk, blocks, approvals, and kill-switch state from backend risk tools.",
    datasets: [
      { label: "Risk overview", load: () => riskClient.getOverview() },
      { label: "Risk blocks", load: () => riskClient.listBlocks() },
      { label: "Risk approvals", load: () => riskClient.listApprovals() },
      { label: "Kill switch", load: () => riskClient.getKillSwitch() },
    ],
  },
  portfolio: {
    title: "Portfolio",
    subtitle: "Portfolio allocation, lifecycle, and recommendation data from backend tools.",
    datasets: [
      { label: "Overview", load: () => portfolioClient.getOverview() },
      { label: "Allocations", load: () => portfolioClient.listAllocations() },
      { label: "Lifecycle", load: () => portfolioClient.getLifecycle() },
      { label: "Recommendations", load: () => portfolioClient.listRecommendations() },
    ],
  },
  execution: {
    title: "Execution",
    subtitle: "Execution readiness, broker health, orders, and incidents from backend tools.",
    datasets: [
      { label: "Readiness", load: () => executionClient.getReadiness() },
      { label: "Broker health", load: () => executionClient.getBrokerHealth() },
      { label: "Orders", load: () => executionClient.listOrders() },
      { label: "Incidents", load: () => executionClient.listIncidents() },
    ],
  },
  "board-room": {
    title: "Board Room",
    subtitle: "Approval queue from backend governance tools.",
    datasets: [
      { label: "Approval queue", load: () => boardClient.listApprovalQueue() },
    ],
  },
  audit: {
    title: "Audit",
    subtitle: "Audit events and findings from backend audit tools.",
    datasets: [
      { label: "Audit events", load: () => auditClient.listAuditEvents() },
    ],
  },
  costs: {
    title: "Costs",
    subtitle: "Cost summary and cost breakdowns from backend cost tools.",
    datasets: [
      { label: "Summary", load: () => costClient.getSummary() },
      { label: "By agent", load: () => costClient.listByAgent() },
      { label: "By workflow", load: () => costClient.listByWorkflow() },
    ],
  },
  settings: {
    title: "Settings",
    subtitle: "Read-only Agentic Firm configuration snapshot from backend settings tools.",
    datasets: [
      { label: "Agentic Firm settings", load: () => settingsClient.getAgenticFirmSnapshot() },
    ],
  },
}

function normalizeRecords(payload: unknown): Array<Record<string, unknown>> {
  if (Array.isArray(payload)) {
    return payload.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object" && !Array.isArray(item))
  }
  if (payload && typeof payload === "object") {
    return [payload as Record<string, unknown>]
  }
  return []
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "-"
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value)
  if (Array.isArray(value)) return value.map(formatCell).join(", ")
  return JSON.stringify(value)
}

function getColumns(records: Array<Record<string, unknown>>): string[] {
  const keys = new Set<string>()
  records.slice(0, 10).forEach((record) => {
    Object.keys(record).slice(0, 8).forEach((key) => keys.add(key))
  })
  return Array.from(keys)
}

export function BackendWorkspacePage({ page }: { page: PageKey }) {
  const definition = pageDefinitions[page]
  const [datasets, setDatasets] = React.useState<Dataset[]>([])
  const [loading, setLoading] = React.useState(true)
  const [loadedAt, setLoadedAt] = React.useState<string | null>(null)

  const load = React.useCallback(async () => {
    setLoading(true)
    const results = await Promise.allSettled(
      definition.datasets.map(async (dataset) => ({
        label: dataset.label,
        records: normalizeRecords(await dataset.load()),
      })),
    )

    setDatasets(
      results.map((result, index) => {
        if (result.status === "fulfilled") return result.value
        return {
          label: definition.datasets[index].label,
          records: [],
          error: result.reason instanceof Error ? result.reason.message : "Backend request failed.",
        }
      }),
    )
    setLoadedAt(new Date().toLocaleString())
    setLoading(false)
  }, [definition])

  React.useEffect(() => {
    void load()
  }, [load])

  const totalRecords = datasets.reduce((sum, dataset) => sum + dataset.records.length, 0)
  const failedDatasets = datasets.filter((dataset) => dataset.error)

  return (
    <main className="space-y-6 p-4 md:p-6">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <Badge variant="outline" className="w-fit">
            Client-backed
          </Badge>
          <div>
            <h1 className="text-3xl font-semibold tracking-normal">{definition.title}</h1>
            <p className="max-w-4xl text-sm text-muted-foreground">{definition.subtitle}</p>
          </div>
        </div>
        <Button variant="outline" onClick={() => void load()} disabled={loading}>
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCcw className="size-4" />}
          Refresh
        </Button>
      </section>

      <section className="grid gap-3 md:grid-cols-3">
        <SummaryCard label="Datasets" value={String(definition.datasets.length)} icon={Database} />
        <SummaryCard label="Backend records" value={loading ? "Loading" : String(totalRecords)} icon={FileText} />
        <SummaryCard label="Last checked" value={loadedAt ?? "Not loaded"} icon={CheckCircle2} />
      </section>

      {failedDatasets.length ? (
        <Card className="border-amber-300 bg-amber-50 text-amber-950 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100">
          <CardContent className="flex items-start gap-3 p-4 text-sm">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" />
            <div>
              <p className="font-medium">Backend data unavailable for {failedDatasets.length} dataset{failedDatasets.length === 1 ? "" : "s"}.</p>
              <p className="mt-1 opacity-80">Seeded placeholder values are no longer shown here. Connect the listed endpoint to populate this page.</p>
            </div>
          </CardContent>
        </Card>
      ) : null}

      <section className="space-y-4">
        {datasets.map((dataset) => (
          <DatasetTable key={dataset.label} dataset={dataset} />
        ))}
      </section>
    </main>
  )
}

function SummaryCard({
  label,
  value,
  icon: Icon,
}: {
  label: string
  value: string
  icon: React.ComponentType<{ className?: string }>
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <div className="flex size-10 items-center justify-center rounded-md bg-muted">
          <Icon className="size-5 text-muted-foreground" />
        </div>
        <div className="min-w-0">
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="truncate text-lg font-semibold">{value}</p>
        </div>
      </CardContent>
    </Card>
  )
}

function DatasetTable({ dataset }: { dataset: Dataset }) {
  const columns = getColumns(dataset.records)

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          <CardTitle className="text-base">{dataset.label}</CardTitle>
          <Badge variant={dataset.error ? "destructive" : "secondary"}>
            {dataset.error ? "unavailable" : `${dataset.records.length} records`}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {dataset.error ? (
          <p className="text-sm text-muted-foreground">{dataset.error}</p>
        ) : dataset.records.length === 0 ? (
          <p className="text-sm text-muted-foreground">No backend records returned.</p>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  {columns.map((column) => (
                    <TableHead key={column}>{column}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {dataset.records.slice(0, 20).map((record, index) => (
                  <TableRow key={String(record.id ?? record.uuid ?? record.name ?? index)}>
                    {columns.map((column) => (
                      <TableCell key={column} className="max-w-[22rem] truncate">
                        {formatCell(record[column])}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
