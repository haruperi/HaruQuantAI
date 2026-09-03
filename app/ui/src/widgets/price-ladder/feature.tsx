"use client";

import { useMemo } from "react";

import {
  resolvePriceLadderConfig,
  type PriceLadderConfig,
} from "./config";
import { PRICE_LADDER_MANIFEST } from "./manifest";
import { PriceLadderWidget } from "./PriceLadderWidget";

/** Props for the FEAT-UI-05 lifecycle adapter. */
export interface PriceLadderFeatureProps {
  /**
   * Raw widget configuration (strict schema); `undefined` selects the
   * documented defaults and invalid input renders an explicit
   * configuration-error state instead of silently passing through.
   */
  readonly config?: unknown;
}

interface ResolvedConfig {
  readonly value: PriceLadderConfig | null;
  readonly error: string | null;
}

function resolveConfig(input: unknown | undefined): ResolvedConfig {
  try {
    return { value: resolvePriceLadderConfig(input), error: null };
  } catch (cause) {
    return {
      value: null,
      error: cause instanceof Error ? cause.message : String(cause),
    };
  }
}

/**
 * FEAT-UI-05 lifecycle adapter: it owns the widget configuration
 * lifecycle and the explicit invalid-configuration response;
 * `PriceLadderWidget` remains focused presentation.
 */
export function PriceLadderFeature({
  config: configInput,
}: PriceLadderFeatureProps): React.JSX.Element {
  const { value: config, error: configError } = useMemo(
    () => resolveConfig(configInput),
    [configInput],
  );

  if (config === null) {
    return (
      <section
        role="alert"
        aria-label={`${PRICE_LADDER_MANIFEST.title} configuration error`}
      >
        <h2>{PRICE_LADDER_MANIFEST.title}</h2>
        <p>
          The widget configuration is invalid and was rejected instead of
          partially applied:
        </p>
        <pre>{configError}</pre>
      </section>
    );
  }

  return (
    <section
      role="region"
      aria-label={PRICE_LADDER_MANIFEST.title}
      style={{ height: "100%", width: "100%" }}
    >
      <PriceLadderWidget
        variant={config.variant}
        symbol={config.defaultSymbol}
        accountId={config.accountId}
      />
    </section>
  );
}
