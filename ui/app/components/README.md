# UI Components

This folder is the sanctioned **universal UI primitives layer** — the frontend
counterpart of the backend rule that shared universal metamodels may be
imported while plugin-specific contracts may not be centralized.

## Boundary law

- Only domain-agnostic presentation primitives live here (`ui.tsx`).
- Domain code never lives in `components/` — every workspace and plugin folder
  owns all of its domain logic, fixtures, and helpers (Locality of Behavior).
- Workspace and plugin folders import from this layer freely, exactly as
  backend plugins import the kernel's universal metamodels; no primitive may
  encode quantitative concepts, another domain's vocabulary, or backend
  contracts.
- Adding or removing any workspace or plugin must never require editing this
  folder (Orthogonality).
