"use client";

import { useMemo } from "react";

import { resolveWatchlistsConfig, type WatchlistsConfig } from "./config";
import { WATCHLISTS_MANIFEST } from "./manifest";
import { WatchlistWidget } from "./WatchlistWidget";

/** Props for the FEAT-UI-03 lifecycle adapter. */
export interface WatchlistsFeatureProps {
  /**
   * Raw widget configuration (strict schema); `undefined` selects the
   * documented defaults and invalid input renders an explicit
   * configuration-error state instead of silently passing through.
   */
  readonly config?: unknown;
}

interface ResolvedConfig {
  readonly value: WatchlistsConfig | null;
  readonly error: string | null;
}

function resolveConfig(input: unknown | undefined): ResolvedConfig {
  try {
    return { value: resolveWatchlistsConfig(input), error: null };
  } catch (cause) {
    return {
      value: null,
      error: cause instanceof Error ? cause.message : String(cause),
    };
  }
}

/**
 * FEAT-UI-03 lifecycle adapter: it owns the widget configuration
 * lifecycle and the explicit invalid-configuration response; the widget
 * renders its own loading/ready/error/unavailable transport states.
 * `WatchlistWidget` remains focused presentation.
 */
export function WatchlistsFeature({
  config: configInput,
}: WatchlistsFeatureProps): React.JSX.Element {
  const { value: config, error: configError } = useMemo(
    () => resolveConfig(configInput),
    [configInput],
  );

  if (config === null) {
    return (
      <section
        role="alert"
        aria-label={`${WATCHLISTS_MANIFEST.title} configuration error`}
      >
        <h2>{WATCHLISTS_MANIFEST.title}</h2>
        <p>
          The widget configuration is invalid and was rejected instead of
          partially applied:
        </p>
        <pre>{configError}</pre>
      </section>
    );
  }

  return <WatchlistWidget />;
}
