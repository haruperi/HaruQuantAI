## FEAT-CONF-01: Centralized model configuration for all ADK agents (app.services.config.agent_model)

| Function | Purpose |
|----------|---------|
| `get_model_for_tier(tier: str) -> str` | Return the model name for a given cost tier. |
| `get_all_model_names() -> list[str]` | Return all configured model names (for validation/metrics). |


## FEAT-CONF-02: Policy configuration loader and resolver (app.services.config.policies)

| Function | Purpose |
|----------|---------|
| `FailureBehavior` (model) | Policy failure behavior options. |
| `LoggingRequirement` (model) | Policy logging requirement options. |
| `EnforcementLayer` (model) | Policy enforcement layer options. |
| `PolicyConfig` (model) | Policy configuration schema. |
| `PolicyResolver.__init__(policy_dir: Path \| None = None) -> None` | Load, validate, and resolve policies by scope. |
| `PolicyResolver.policies -> dict[str, PolicyConfig]` | Load, validate, and resolve policies by scope. |
| `PolicyResolver.load_all() -> None` | Load all YAML policy files from the policy directory. |
| `PolicyResolver.resolve_for_scope(scope: str) -> list[PolicyConfig]` | Return all policies that apply to the given scope. |
| `PolicyResolver.get_by_name(name: str) -> PolicyConfig \| None` | Return a single policy by name. |
| `PolicyResolver.should_enforce(scope: str, layer: EnforcementLayer) -> list[PolicyConfig]` | Return policies that apply to scope AND enforcement layer. |
| `PolicyResolver.on_failure(scope: str) -> FailureBehavior \| None` | Return the failure behavior for the first matching policy. |
| `PolicyResolver.reload() -> None` | Reload all policies (useful for hot-reload scenarios). |

