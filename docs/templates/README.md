# [Plugin Family] Plugin Package

> **Package:** `app/plugins/[kind]/`
> **Plugin kind:** `[kind]`
> **Status:** `[Missing | Partial | Complete]`
> **Last verified revision:** `[commit SHA]`

This README documents shared policy for one plugin family. It must not duplicate
the executable parameter schema, bounds, outputs, UI metadata, or behavior of an
individual plugin. Each concrete plugin file is its own source of truth.

## 1. Family responsibility

[Describe what concepts belong to this family and the outcome they provide.]

### Owns

- [Shared responsibility]

### Does not own

- [Responsibility belonging to host, UI, or another family]

## 2. Physical structure

```text
app/plugins/[kind]/
|-- __init__.py              # empty or docstring-only
|-- README.md                # this shared family policy
|-- [plugin_a].py            # complete concrete plugin A
`-- [plugin_b].py            # complete concrete plugin B
```

Forbidden companion production files include plugin-specific `models.py`,
`schemas.py`, `contracts.py`, `optimization.py`, `ui.py`, or exporter fragments.

## 3. Universal API and allowed imports

- **Universal plugin API:** `[path and version]`
- **Approved numerical foundations:** `[libraries or standard library]`
- **Allowed host capabilities:** `[typed slots]`
- **Forbidden imports:** host implementations, UI, registry, sibling plugins,
  private modules, and plugin-specific centralized contracts.

## 4. Shared semantic policy

Document only rules common to every plugin in this family:

- input/output units and type vocabulary;
- warm-up and missing-data baseline;
- numerical precision and non-finite policy;
- determinism and seed policy;
- legal algebra placement;
- generic error taxonomy;
- resource/effect restrictions.

Any exception belongs explicitly in the concrete plugin file.

## 5. Plugin index

This table is descriptive and should be generated or verified from the catalog.
Do not copy parameter lists or behavior here.

| Stable ID | Production file | Version | Provides/node kind | Status | Evidence |
|---|---|---|---|---|---|
| `[family.plugin]` | `[plugin].py` | `[version]` | `[contribution]` | `[status]` | `[link]` |

## 6. Discovery and enablement

- Discovery root: `[path]`
- Factory/contribution symbol: `[symbol]`
- Canonical ordering: `[rule]`
- Default enablement: `[disabled/approved profile]`
- Duplicate/incompatible behavior: fail catalog publication.
- Removal behavior: preserve referencing documents as explicitly unavailable.

Installing a plugin never requires editing this README, a central registry,
engine code, or UI source. The index may be regenerated as evidence.

## 7. Algebra and consumer obligations

| Consumer | Uses | Prohibited duplication | Acceptance |
|---|---|---|---|
| UI | Catalog schema/ports | Plugin-specific form definitions | [test] |
| Generator | Schema/algebra | Independent grammar meaning | [test] |
| Simulator | Behavior/ports | String-expression reinterpretation | [test] |
| Optimizer | Declared bounds | Separate optimization spaces | [test] |
| Exporter | Declared lowering | Divergent semantics | [test] |

## 8. Testing and usage evidence

Required per-plugin evidence:

- construction/schema/identity tests;
- hand-golden and edge tests;
- determinism and serialization round-trip;
- discovery and disabled-by-default behavior;
- add/remove orthogonality;
- claimed consumer parity;
- deterministic offline usage example;
- current source-bound acceptance manifest.

Focused command:

```powershell
uv run pytest --no-cov tests/plugins/[kind]/test_[plugin].py -v
```

## 9. Family completion checklist

- [ ] Every concrete concept is one cohesive plugin file.
- [ ] No plugin-specific schema or behavior is duplicated outside its file.
- [ ] Discovery requires no central source edit.
- [ ] Every ID/version is canonical and unique.
- [ ] Every plugin is disabled by default unless policy explicitly enables it.
- [ ] Every claimed consumer uses the same catalog/algebra semantics.
- [ ] Removal leaves unrelated plugins and documents unchanged.
- [ ] Tests, usage evidence, and acceptance manifests are current.
- [ ] Plugin Implementation Audit reports no unresolved FAIL.

## 10. Open decisions

| Status | Decision | Evidence needed | Owner |
|---|---|---|---|
| Open | `[decision]` | `[evidence]` | `[owner]` |
