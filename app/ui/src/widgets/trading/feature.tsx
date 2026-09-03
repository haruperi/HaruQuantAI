"use client";

import { useMemo } from "react";

import {
  resolveTradingConfig,
  type TradingConfig,
} from "./config";
import { TRADING_MANIFEST } from "./manifest";
import { TradingWidget } from "./TradingWidget";

/** Props for the FEAT-UI-06 lifecycle adapter. */
export interface TradingFeatureProps {
  /**
   * Raw widget configuration (strict schema); `undefined` selects the
   * documented defaults and invalid input renders an explicit
   * configuration-error state instead of silently passing through.
   */
  readonly config?: unknown;
  readonly className?: string;
}

interface ResolvedConfig {
  readonly value: TradingConfig | null;
  readonly error: string | null;
}

function resolveConfig(input: unknown | undefined): ResolvedConfig {
  try {
    return { value: resolveTradingConfig(input), error: null };
  } catch (cause) {
    return {
      value: null,
      error: cause instanceof Error ? cause.message : String(cause),
    };
  }
}

/**
 * FEAT-UI-06 lifecycle adapter: it owns the widget configuration
 * lifecycle and the explicit invalid-configuration response; `TradingWidget`
 * remains focused presentation.
 */
export function TradingFeature({
  config: configInput,
  className,
}: TradingFeatureProps): React.JSX.Element {
  const { value: config, error: configError } = useMemo(
    () => resolveConfig(configInput),
    [configInput],
  );

  if (config === null) {
    return (
      <section
        role="alert"
        aria-label={`${TRADING_MANIFEST.title} configuration error`}
      >
        <h2>{TRADING_MANIFEST.title}</h2>
        <p>
          The widget configuration is invalid and was rejected instead of
          partially applied:
        </p>
        <pre>{configError}</pre>
      </section>
    );
  }

  return (
    <TradingWidget
      className={className}
      symbol={config.defaultSymbol}
      ticketHostOnly={config.ticketHostOnly}
      accountId={config.accountId}
    />
  );
}
