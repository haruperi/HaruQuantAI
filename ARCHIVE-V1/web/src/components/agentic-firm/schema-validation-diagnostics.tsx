import { AlertTriangle } from "lucide-react"
import type { ZodIssue } from "zod"

import { formatValidationIssues } from "@/validators/agentic-contracts"

interface SchemaValidationDiagnosticsProps {
  contractName: string
  issues: ZodIssue[]
}

export function SchemaValidationDiagnostics({
  contractName,
  issues,
}: SchemaValidationDiagnosticsProps) {
  if (issues.length === 0) {
    return null
  }

  return (
    <details className="rounded border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
      <summary className="flex cursor-pointer items-center gap-2 font-medium text-amber-800 dark:text-amber-200">
        <AlertTriangle className="h-4 w-4" />
        {contractName} schema validation failed
      </summary>
      <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
        {formatValidationIssues(issues).map((issue) => (
          <li key={issue}>{issue}</li>
        ))}
      </ul>
    </details>
  )
}
