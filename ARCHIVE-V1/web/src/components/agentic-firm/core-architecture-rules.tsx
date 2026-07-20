import { CheckCircle2, ShieldCheck } from "lucide-react"

import { CORE_UI_ARCHITECTURE_RULES } from "@/types/agentic-core"

export function CoreArchitectureRules() {
  return (
    <section className="grid gap-4 md:grid-cols-2">
      {CORE_UI_ARCHITECTURE_RULES.map((group) => (
        <article key={group.id} className="rounded border bg-background p-4">
          <div className="flex items-start gap-3">
            <div className="rounded border bg-muted/40 p-2">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium uppercase text-muted-foreground">
                Authority: {group.authority.replace("_", " ")}
              </p>
              <h2 className="text-sm font-semibold">{group.title}</h2>
            </div>
          </div>
          <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
            {group.rules.map((rule) => (
              <li key={rule} className="flex gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                <span>{rule}</span>
              </li>
            ))}
          </ul>
        </article>
      ))}
    </section>
  )
}
