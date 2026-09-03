"use client";

import { useMemo } from "react";

import {
  resolveTradeLogConfig,
  type TradeLogConfig,
} from "./config";
import { TRADE_LOG_MANIFEST } from "./manifest";
import { TradeLogWidget } from "./TradeLogWidget";

/** Props for the FEAT-UI-08 lifecycle adapter. */
export interface TradeLogFeatureProps {
  /**
   * Raw widget configuration (strict schema); `undefined` selects the
   * documented defaults and invalid input renders an explicit
   * configuration-error state instead of silently passing through.
   */
  readonly config?: unknown;
}

interface ResolvedConfig {
  readonly value: TradeLogConfig | null;
  readonly error: string | null;
}

function resolveConfig(input: unknown | undefined): ResolvedConfig {
  try {
    return { value: resolveTradeLogConfig(input), error: null };
  } catch (cause) {
    return {
      value: null,
      error: cause instanceof Error ? cause.message : String(cause),
    };
  }
}

/**
 * FEAT-UI-08 lifecycle adapter: it owns the widget configuration
 * lifecycle and the explicit invalid-configuration response;
 * `TradeLogWidget` remains focused presentation.
 */
export function TradeLogFeature({
  config: configInput,
}: TradeLogFeatureProps): React.JSX.Element {
  const { value: config, error: configError } = useMemo(
    () => resolveConfig(configInput),
    [configInput],
  );

  if (config === null) {
    return (
      <section
        role="alert"
        aria-label={`${TRADE_LOG_MANIFEST.title} configuration error`}
      >
        <h2>{TRADE_LOG_MANIFEST.title}</h2>
        <p>
          The widget configuration is invalid and was rejected instead of
          partially applied:
        </p>
        <pre>{configError}</pre>
      </section>
    );
  }

  return <TradeLogWidget initialProduct={config.defaultProduct} />;
}
