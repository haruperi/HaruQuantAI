# FEAT-BRK-CONNECT_YAHOO — Yahoo Provider

Read-only, sandbox-only Yahoo provider feature. A caller must configure an explicit
probe symbol; the feature never invents provider symbols or accepts account/order
operations. Removing the feature removes Yahoo behavior without changing another
provider or the dispatcher.

Provides only `broker.provider.yahoo@1`.
