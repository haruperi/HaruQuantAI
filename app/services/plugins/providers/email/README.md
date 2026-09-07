# Email Notification Delivery Provider

> **Provider ID:** `notification.delivery.email`
> **Capability:** `notification.delivery.v1`
> **Lifecycle:** Scoped, `reversible_ephemeral`
> **Status:** Adapter implemented; backend readiness is configuration-dependent

## Overview

Adapts an injected, lifecycle-scoped SMTP backend to `NotificationDeliveryCapabilityV1`.
The provider never imports a removed utility implementation or performs I/O at import time.
