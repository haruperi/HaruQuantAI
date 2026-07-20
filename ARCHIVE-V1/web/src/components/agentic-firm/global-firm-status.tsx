"use client"

import * as React from "react"
import Link from "next/link"
import {
  AlertTriangle,
  BadgeAlert,
  Bell,
  Bot,
  Clock3,
  DollarSign,
  HeartPulse,
  KeyRound,
  Network,
  ShieldAlert,
  ShieldCheck,
  UserCircle,
  Zap,
} from "lucide-react"

import { boardClient } from "@/clients/boardClient"
import { executionClient } from "@/clients/executionClient"
import { portfolioClient } from "@/clients/portfolioClient"
import { riskClient } from "@/clients/riskClient"
import { workflowClient } from "@/clients/workflowClient"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth-context"
import { trackAgenticTelemetry } from "@/lib/agentic-firm/telemetry"

type StatusTone = "good" | "watch" | "bad" | "neutral"

type StatusItem = {
  label: string
  value: string
  tone: StatusTone
  icon: React.ComponentType<{ className?: string }>
  href?: string
}

type AlertItem = {
  title: string
  detail: string
  tone: "warning" | "critical" | "info"
  href: string
  icon: React.ComponentType<{ className?: string }>
}

const initialStatusItems: StatusItem[] = [
  { label: "Environment", value: "checking", tone: "neutral", icon: Bot, href: "/settings" },
  { label: "Execution", value: "checking", tone: "neutral", icon: Zap, href: "/execution" },
  { label: "Live", value: "checking", tone: "neutral", icon: ShieldAlert, href: "/execution" },
  { label: "Kill switch", value: "checking", tone: "neutral", icon: ShieldCheck, href: "/risk-center" },
  { label: "RiskGovernor", value: "checking", tone: "neutral", icon: HeartPulse, href: "/risk-center" },
  { label: "Broker heartbeat", value: "checking", tone: "neutral", icon: Network, href: "/execution" },
  { label: "Audit", value: "checking", tone: "neutral", icon: KeyRound, href: "/audit" },
  { label: "Drawdown", value: "checking", tone: "neutral", icon: AlertTriangle, href: "/risk-center" },
  { label: "Daily P&L", value: "checking", tone: "neutral", icon: DollarSign, href: "/portfolio" },
  { label: "Exposure", value: "checking", tone: "neutral", icon: BadgeAlert, href: "/portfolio" },
  { label: "Workflows", value: "checking", tone: "neutral", icon: Clock3, href: "/agents" },
  { label: "Approvals", value: "checking", tone: "neutral", icon: Bell, href: "/board-room" },
]

function valueFromRecord(record: unknown, keys: string[], fallback = "unavailable") {
  if (!record || typeof record !== "object" || Array.isArray(record)) return fallback
  const typed = record as Record<string, unknown>
  for (const key of keys) {
    const value = typed[key]
    if (value !== undefined && value !== null) return String(value)
  }
  return fallback
}

function toneFor(value: string): StatusTone {
  const normalized = value.toLowerCase()
  if (normalized.includes("unavailable") || normalized.includes("failed") || normalized.includes("blocked")) return "bad"
  if (normalized.includes("disabled") || normalized.includes("stale") || normalized.includes("partial")) return "watch"
  if (normalized.includes("available") || normalized.includes("ok") || normalized.includes("healthy")) return "good"
  return "neutral"
}

export function GlobalFirmStatus() {
  const { user } = useAuth()
  const [statusItems, setStatusItems] = React.useState(initialStatusItems)
  const [alerts, setAlerts] = React.useState<AlertItem[]>([])
  const userLabel = user?.full_name || user?.username || user?.email || "signed-in user"
  const criticalAlerts = alerts.filter((alert) => alert.tone === "critical")
  const visibleStatus = statusItems.filter((item) =>
    ["Environment", "Execution", "Live", "Kill switch"].includes(item.label)
  )

  React.useEffect(() => {
    let cancelled = false

    async function loadStatus() {
      const [readiness, brokerHealth, killSwitch, riskOverview, portfolio, workflows, approvals] =
        await Promise.allSettled([
          executionClient.getReadiness(),
          executionClient.getBrokerHealth(),
          riskClient.getKillSwitch(),
          riskClient.getOverview(),
          portfolioClient.getOverview(),
          workflowClient.listWorkflows(),
          boardClient.listApprovalQueue(),
        ])

      if (cancelled) return

      const nextAlerts: AlertItem[] = []
      const readinessData = readiness.status === "fulfilled" ? readiness.value : null
      const brokerData = brokerHealth.status === "fulfilled" ? brokerHealth.value : null
      const killSwitchData = killSwitch.status === "fulfilled" ? killSwitch.value : null
      const riskData = riskOverview.status === "fulfilled" ? riskOverview.value : null
      const portfolioData = portfolio.status === "fulfilled" ? portfolio.value : null
      const workflowData = workflows.status === "fulfilled" ? workflows.value : []
      const approvalData = approvals.status === "fulfilled" ? approvals.value : []

      const failed = [
        ["Execution readiness", readiness, "/execution", Zap],
        ["Broker heartbeat", brokerHealth, "/execution", Network],
        ["Kill switch", killSwitch, "/risk-center", ShieldAlert],
        ["Risk overview", riskOverview, "/risk-center", HeartPulse],
        ["Portfolio overview", portfolio, "/portfolio", BadgeAlert],
        ["Workflows", workflows, "/agents", Clock3],
        ["Approvals", approvals, "/board-room", Bell],
      ] as const

      failed.forEach(([title, result, href, Icon]) => {
        if (result.status === "rejected") {
          nextAlerts.push({
            title: `${title} unavailable`,
            detail: result.reason instanceof Error ? result.reason.message : "Backend request failed.",
            tone: "warning",
            href,
            icon: Icon,
          })
        }
      })

      const executionValue = valueFromRecord(readinessData, ["execution_mode", "mode", "status"])
      const liveValue = valueFromRecord(readinessData, ["live_mode", "live_enabled", "live_status"])
      const killSwitchValue = valueFromRecord(killSwitchData, ["status", "state", "armed", "active"])
      const riskGovernorValue = valueFromRecord(riskData, ["risk_governor_status", "riskGovernor", "status"])
      const brokerValue = valueFromRecord(brokerData, ["heartbeat", "status", "state"])

      setStatusItems([
        { label: "Environment", value: process.env.NEXT_PUBLIC_API_URL ? "api configured" : "api default", tone: "neutral", icon: Bot, href: "/settings" },
        { label: "Execution", value: executionValue, tone: toneFor(executionValue), icon: Zap, href: "/execution" },
        { label: "Live", value: liveValue, tone: toneFor(liveValue), icon: ShieldAlert, href: "/execution" },
        { label: "Kill switch", value: killSwitchValue, tone: toneFor(killSwitchValue), icon: ShieldCheck, href: "/risk-center" },
        { label: "RiskGovernor", value: riskGovernorValue, tone: toneFor(riskGovernorValue), icon: HeartPulse, href: "/risk-center" },
        { label: "Broker heartbeat", value: brokerValue, tone: toneFor(brokerValue), icon: Network, href: "/execution" },
        { label: "Audit", value: "client-backed", tone: "neutral", icon: KeyRound, href: "/audit" },
        { label: "Drawdown", value: valueFromRecord(riskData, ["drawdown", "current_drawdown", "max_drawdown"]), tone: "neutral", icon: AlertTriangle, href: "/risk-center" },
        { label: "Daily P&L", value: valueFromRecord(portfolioData, ["daily_pnl", "dailyPnL", "pnl"]), tone: "neutral", icon: DollarSign, href: "/portfolio" },
        { label: "Exposure", value: valueFromRecord(portfolioData, ["exposure", "open_exposure", "total_exposure"]), tone: "neutral", icon: BadgeAlert, href: "/portfolio" },
        { label: "Workflows", value: `${Array.isArray(workflowData) ? workflowData.length : 0} records`, tone: "neutral", icon: Clock3, href: "/agents" },
        { label: "Approvals", value: `${Array.isArray(approvalData) ? approvalData.length : 0} records`, tone: "neutral", icon: Bell, href: "/board-room" },
      ])
      setAlerts(nextAlerts)
    }

    void loadStatus()

    return () => {
      cancelled = true
    }
  }, [])

  React.useEffect(() => {
    const liveStatus = statusItems.find((item) => item.label === "Live")
    const killSwitchStatus = statusItems.find((item) => item.label === "Kill switch")
    const riskGovernorStatus = statusItems.find((item) => item.label === "RiskGovernor")

    trackAgenticTelemetry("agentic.live_mode_visibility", {
      visible: Boolean(liveStatus),
      value: liveStatus?.value,
    })
    trackAgenticTelemetry("agentic.execution_button_render", {
      surface: "global_status",
      enabled: false,
      reason: "execution controls are routed through governed workflow pages",
    })
    trackAgenticTelemetry("agentic.kill_switch_banner_display", {
      visible: Boolean(killSwitchStatus),
      value: killSwitchStatus?.value,
    })
    trackAgenticTelemetry("agentic.risk_governor_unavailable_display", {
      visible: riskGovernorStatus?.tone === "bad",
      value: riskGovernorStatus?.value,
    })

    alerts
      .filter((alert) => alert.title === "Stale data")
      .forEach((alert) => {
        trackAgenticTelemetry("agentic.stale_data", {
          source: alert.href,
          reason: alert.detail,
        })
      })
  }, [alerts, statusItems])

  return (
    <div className="border-b bg-background">
      <section className="flex min-h-9 items-center gap-2 overflow-x-auto px-4 py-1.5 md:px-6">
        {visibleStatus.map((item) => (
          <StatusPill key={`${item.label}-${item.href ?? item.value}`} item={item} />
        ))}
        <StatusPill
          item={{
            label: "Critical",
            value: `${criticalAlerts.length}`,
            tone: criticalAlerts.length ? "bad" : "good",
            icon: AlertTriangle,
            href: "/audit",
          }}
        />
        <FirmStatusMenu userLabel={userLabel} alerts={alerts} statusItems={statusItems} />
      </section>
    </div>
  )
}

function FirmStatusMenu({
  userLabel,
  alerts,
  statusItems,
}: {
  userLabel: string
  alerts: AlertItem[]
  statusItems: StatusItem[]
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="ml-auto h-7 shrink-0 gap-2 rounded-md px-2.5 text-xs">
          <HeartPulse className="size-3.5" />
          Firm Status
          <Badge variant="secondary" className="h-5 px-1.5 text-[10px]">
            {alerts.length}
          </Badge>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[min(92vw,720px)] p-0">
        <div className="max-h-[72vh] overflow-y-auto p-3">
          <DropdownMenuLabel className="px-0 text-xs text-muted-foreground">
            Global status
          </DropdownMenuLabel>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {statusItems.map((item) => (
              <StatusSummary key={`${item.label}-${item.href ?? item.value}`} item={item} />
            ))}
            <StatusSummary
              item={{
                label: "Session",
                value: userLabel,
                tone: "neutral",
                icon: UserCircle,
                href: "/settings",
              }}
            />
            <StatusSummary
              item={{
                label: "Critical alerts",
                value: `${alerts.filter((alert) => alert.tone === "critical").length}`,
                tone: alerts.some((alert) => alert.tone === "critical") ? "bad" : "good",
                icon: AlertTriangle,
                href: "/audit",
              }}
            />
          </div>
          <DropdownMenuSeparator className="my-3" />
          <DropdownMenuLabel className="px-0 text-xs text-muted-foreground">
            Alerts
          </DropdownMenuLabel>
          <div className="space-y-2">
            <AlertStub title="Kill switch triggered" detail="No active trigger." tone="info" icon={ShieldCheck} href="/risk-center" muted />
            <AlertStub title="Critical audit failure" detail="No critical audit failure." tone="info" icon={ShieldCheck} href="/audit" muted />
            {alerts.map((alert) => (
              <AlertStub key={`${alert.title}-${alert.href}`} {...alert} />
            ))}
          </div>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function StatusPill({ item }: { item: StatusItem }) {
  const Icon = item.icon
  const content = (
    <span
      className={cn(
        "flex min-w-max items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs",
        item.tone === "good" && "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-100",
        item.tone === "watch" && "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100",
        item.tone === "bad" && "border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-100",
        item.tone === "neutral" && "border-border bg-background text-muted-foreground"
      )}
    >
      <Icon className="size-3.5 shrink-0" />
      <span className="text-muted-foreground">{item.label}</span>
      <span className="font-medium text-foreground">{item.value}</span>
    </span>
  )

  if (!item.href) return content

  return (
    <Link href={item.href} className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
      {content}
    </Link>
  )
}

function StatusSummary({ item }: { item: StatusItem }) {
  const Icon = item.icon
  return (
    <Link
      href={item.href ?? "#"}
      className={cn(
        "flex items-center gap-2 rounded-md border p-2 text-xs transition-colors hover:bg-accent",
        item.tone === "good" && "border-emerald-200 bg-emerald-50/70 dark:border-emerald-900 dark:bg-emerald-950/60",
        item.tone === "watch" && "border-amber-200 bg-amber-50/70 dark:border-amber-900 dark:bg-amber-950/60",
        item.tone === "bad" && "border-red-200 bg-red-50/70 dark:border-red-900 dark:bg-red-950/60",
        item.tone === "neutral" && "border-border bg-background"
      )}
    >
      <Icon className="size-4 shrink-0 text-muted-foreground" />
      <span className="min-w-0">
        <span className="block truncate text-muted-foreground">{item.label}</span>
        <span className="block truncate font-medium text-foreground">{item.value}</span>
      </span>
    </Link>
  )
}

function AlertStub({
  title,
  detail,
  tone,
  href,
  icon: Icon,
  muted = false,
}: AlertItem & { muted?: boolean }) {
  return (
    <Button
      asChild
      variant="outline"
      size="sm"
      className={cn(
        "h-auto w-full justify-start gap-2 whitespace-normal rounded-md px-3 py-2 text-left",
        muted && "opacity-70",
        tone === "critical" && "border-red-300 bg-red-50 text-red-900 hover:bg-red-100 dark:border-red-900 dark:bg-red-950 dark:text-red-100",
        tone === "warning" && "border-amber-300 bg-amber-50 text-amber-900 hover:bg-amber-100 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100",
        tone === "info" && "border-border bg-background"
      )}
    >
      <Link href={href}>
        <Icon className="mt-0.5 size-4 shrink-0" />
        <span className="min-w-0">
          <span className="flex items-center gap-2 text-xs font-semibold">
            {title}
            <Badge variant={tone === "critical" ? "destructive" : "secondary"} className="text-[10px]">
              {tone}
            </Badge>
          </span>
          <span className="mt-0.5 block text-xs opacity-80">{detail}</span>
        </span>
      </Link>
    </Button>
  )
}
