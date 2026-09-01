# SMS Notification Delivery Provider

> **Provider ID:** `notification.delivery.sms`
> **Capability:** `notification.delivery.v1`
> **Lifecycle:** Scoped, `reversible_ephemeral`
> **Status:** Active

## Overview
Implements Twilio SMS notification delivery capability adhering to `NotificationDeliveryCapabilityV1`.
Lifecycle cleanups release underlying transport resources.
