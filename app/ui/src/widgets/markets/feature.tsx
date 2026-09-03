"use client";

import { useMemo } from "react";

import { resolveMarketsConfig, type MarketsConfig } from "./config";
import { MARKETS_MANIFEST } from "./manifest";
import { MarketsWidget } from "./MarketsWidget";

/** Props for the FEAT-UI-02 lifecycle adapter. */
export interface MarketsFeatureProps {
  /**
   * Raw widget configuration (strict schema); `undefined` selects the
   * documented defaults and invalid input renders an explicit
   * configuration-error state instead of silently passing through.
   */
  readonly config?: unknown;
}

interface ResolvedConfig {
  readonly value: MarketsConfig | null;
  readonly error: string | null;
}

function resolveConfig(input: unknown | undefined): ResolvedConfig {
  try {
    return { value: resolveMarketsConfig(input), error: null };
  } catch (cause) {
    return {
      value: null,
      error: cause instanceof Error ? cause.message : String(cause),
    };
  }
}

/**
 * FEAT-UI-02 lifecycle adapter: it owns the widget configuration
 * lifecycle and the explicit availability response (the widget renders
 * its own loading/settling/ready/error/unavailable transport states).
 * `MarketsWidget` remains focused presentation.
 */
export function MarketsFeature({
  config: configInput,
}: MarketsFeatureProps): React.JSX.Element {
  const { value: config, error: configError } = useMemo(
    () => resolveConfig(configInput),
    [configInput],
  );

  if (config === null) {
    return (
      <section
        role="alert"
        aria-label={`${MARKETS_MANIFEST.title} configuration error`}
      >
        <h2>{MARKETS_MANIFEST.title}</h2>
        <p>
          The widget configuration is invalid and was rejected instead of
          partially applied:
        </p>
        <pre>{configError}</pre>
      </section>
    );
  }

  return (
    <MarketsWidget
      streamSettlingMs={config.streamSettlingSeconds * 1_000}
      pageSize={config.pageSize}
      maxPages={config.maxPages}
    />
  );
}
