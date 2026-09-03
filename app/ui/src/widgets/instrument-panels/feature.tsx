"use client";

import { OptionsGridWidget } from "./OptionsGridWidget";

import { INSTRUMENT_PANELS_MANIFEST } from "./manifest";

/** Props for the FEAT-UI-19 lifecycle adapter. */
export interface InstrumentPanelsFeatureProps {
  /** Instrument symbol for the panel grid. */
  readonly symbol?: string;
}

/**
 * FEAT-UI-19 lifecycle adapter. The panels render local labelled values
 * with no backend capability; the adapter exposes the manifest identity
 * and forwards the symbol to the focused presentation.
 */
export function InstrumentPanelsFeature({
  symbol,
}: InstrumentPanelsFeatureProps): React.JSX.Element {
  return <OptionsGridWidget symbol={symbol} />;
}

export { INSTRUMENT_PANELS_MANIFEST };
