"use client";

import { useMemo } from "react";

import {
  resolveTradePlanConfig,
  type TradePlanConfig,
} from "./config";
import { TRADE_PLAN_MANIFEST } from "./manifest";
import { TradePlanWidget } from "./TradePlanWidget";

/** Props for the FEAT-UI-10 lifecycle adapter. */
export interface TradePlanFeatureProps {
  /**
   * Raw widget configuration (strict schema); `undefined` selects the
   * documented defaults and invalid input renders an explicit
   * configuration-error state instead of silently passing through.
   */
  readonly config?: unknown;
}

interface ResolvedConfig {
  readonly value: TradePlanConfig | null;
  readonly error: string | null;
}

function resolveConfig(input: unknown | undefined): ResolvedConfig {
  try {
    return { value: resolveTradePlanConfig(input), error: null };
  } catch (cause) {
    return {
      value: null,
      error: cause instanceof Error ? cause.message : String(cause),
    };
  }
}

/**
 * FEAT-UI-10 lifecycle adapter: it owns the widget configuration
 * lifecycle and the explicit invalid-configuration response;
 * `TradePlanWidget` remains focused presentation.
 */
export function TradePlanFeature({
  config: configInput,
}: TradePlanFeatureProps): React.JSX.Element {
  const { value: config, error: configError } = useMemo(
    () => resolveConfig(configInput),
    [configInput],
  );

  if (config === null) {
    return (
      <section
        role="alert"
        aria-label={`${TRADE_PLAN_MANIFEST.title} configuration error`}
      >
        <h2>{TRADE_PLAN_MANIFEST.title}</h2>
        <p>
          The widget configuration is invalid and was rejected instead of
          partially applied:
        </p>
        <pre>{configError}</pre>
      </section>
    );
  }

  return (
    <TradePlanWidget
      initialRiskRewardRatio={config.defaultRiskRewardRatio}
    />
  );
}
