"use client";

import { useMemo } from "react";

import {
  resolvePositionsConfig,
  type PositionsConfig,
} from "./config";
import { POSITIONS_MANIFEST } from "./manifest";
import { PositionsWidget } from "./PositionsWidget";

/** Props for the FEAT-UI-09 lifecycle adapter. */
export interface PositionsFeatureProps {
  /**
   * Raw widget configuration (strict schema); `undefined` selects the
   * documented defaults and invalid input renders an explicit
   * configuration-error state instead of silently passing through.
   */
  readonly config?: unknown;
}

interface ResolvedConfig {
  readonly value: PositionsConfig | null;
  readonly error: string | null;
}

function resolveConfig(input: unknown | undefined): ResolvedConfig {
  try {
    return { value: resolvePositionsConfig(input), error: null };
  } catch (cause) {
    return {
      value: null,
      error: cause instanceof Error ? cause.message : String(cause),
    };
  }
}

/**
 * FEAT-UI-09 lifecycle adapter: it owns the widget configuration
 * lifecycle and the explicit invalid-configuration response;
 * `PositionsWidget` remains focused presentation.
 */
export function PositionsFeature({
  config: configInput,
}: PositionsFeatureProps): React.JSX.Element {
  const { value: config, error: configError } = useMemo(
    () => resolveConfig(configInput),
    [configInput],
  );

  if (config === null) {
    return (
      <section
        role="alert"
        aria-label={`${POSITIONS_MANIFEST.title} configuration error`}
      >
        <h2>{POSITIONS_MANIFEST.title}</h2>
        <p>
          The widget configuration is invalid and was rejected instead of
          partially applied:
        </p>
        <pre>{configError}</pre>
      </section>
    );
  }

  return <PositionsWidget initialTab={config.defaultTab} />;
}
