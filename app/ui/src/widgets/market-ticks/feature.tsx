"use client";

import { useMemo } from "react";

import { resolveMarketTicksConfig, type MarketTicksConfig } from "./config";
import { MARKET_TICKS_MANIFEST } from "./manifest";
import { MarketTicksTableWidget } from "./MarketTicksTableWidget";
import { useMarketSnapshots } from "./useMarketSnapshots";

/** Props for the FEAT-UI-25 lifecycle adapter. */
export interface MarketTicksFeatureProps {
  /**
   * Raw widget configuration (strict schema); `undefined` selects the
   * documented defaults and invalid input renders an explicit
   * configuration-error state instead of silently passing through.
   */
  readonly config?: unknown;
}

interface ResolvedConfig {
  readonly value: MarketTicksConfig | null;
  readonly error: string | null;
}

function resolveConfig(input: unknown | undefined): ResolvedConfig {
  try {
    return { value: resolveMarketTicksConfig(input), error: null };
  } catch (cause) {
    return {
      value: null,
      error: cause instanceof Error ? cause.message : String(cause),
    };
  }
}

/**
 * FEAT-UI-25 lifecycle adapter: it owns the widget configuration
 * lifecycle, the observation subscription lifecycle (start, cancel,
 * exact disposal via the hook's abort cleanup), and the explicit
 * availability response. `MarketTicksTableWidget` remains focused
 * presentation and renders no transport.
 */
export function MarketTicksFeature({
  config: configInput,
}: MarketTicksFeatureProps): React.JSX.Element {
  const { value: config, error: configError } = useMemo(
    () => resolveConfig(configInput),
    [configInput],
  );
  const { snapshot, status, error } = useMarketSnapshots(
    config === null
      ? { enabled: false }
      : {
          symbols: config.symbols,
          initialRetryMs: config.reconnectInitialDelayMs,
          maxRetryMs: config.reconnectMaxDelayMs,
        },
  );

  if (config === null) {
    return (
      <section
        role="alert"
        aria-label={`${MARKET_TICKS_MANIFEST.title} configuration error`}
      >
        <h2>{MARKET_TICKS_MANIFEST.title}</h2>
        <p>
          The widget configuration is invalid and was rejected instead of
          partially applied:
        </p>
        <pre>{configError}</pre>
      </section>
    );
  }

  return (
    <MarketTicksTableWidget
      snapshot={snapshot}
      status={status}
      error={error}
      staleRowAfterSeconds={config.staleRowAfterSeconds}
    />
  );
}
