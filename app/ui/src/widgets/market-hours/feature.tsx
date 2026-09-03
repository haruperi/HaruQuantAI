"use client";

import { MarketHoursWidget } from "./MarketHoursWidget";
import { MARKET_HOURS_MANIFEST } from "./manifest";

/**
 * FEAT-UI-30 lifecycle adapter. The widget owns its typed configuration
 * surface (`MarketHoursWidgetConfig` with documented defaults) and
 * consumes no backend capability; the adapter exposes the manifest
 * identity and renders the focused presentation.
 */
export function MarketHoursFeature(): React.JSX.Element {
  return <MarketHoursWidget />;
}

export { MARKET_HOURS_MANIFEST };
