# Deliver Notifications

`FEAT-ORCH-DELIVER_NOTIFICATIONS` owns idempotent notification coordination, the master and
channel enablement gates, durable receipts, bounded rate policy, pre-transport redaction, and
uncertain-outcome disclosure. Transport providers implement `notification.delivery@1`; they do
not own orchestration policy or receipt persistence.

This package closes the former unified-notification utility gap. The broader feature card in the
domain README remains `Partial`; account-backed recipient resolution, audited test-send settings,
the Workspace persistence capability, and qualified external backends still require their planned
feature work and end-to-end acceptance evidence.

Run the offline example with:

```console
uv run python -m app.services.orchestration.deliver_notifications._usage
```
