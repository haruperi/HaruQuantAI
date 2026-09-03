"use client";

import { useMemo } from "react";

import { resolveNewsConfig, type NewsConfig } from "./config";
import { NEWS_MANIFEST } from "./manifest";
import { NewsWidget } from "./NewsWidget";

/** Props for the FEAT-UI-29 lifecycle adapter. */
export interface NewsFeatureProps {
  /**
   * Raw widget configuration (strict schema); `undefined` selects the
   * documented defaults and invalid input renders an explicit
   * configuration-error state instead of silently passing through.
   */
  readonly config?: unknown;
}

interface ResolvedConfig {
  readonly value: NewsConfig | null;
  readonly error: string | null;
}

function resolveConfig(input: unknown | undefined): ResolvedConfig {
  try {
    return { value: resolveNewsConfig(input), error: null };
  } catch (cause) {
    return {
      value: null,
      error: cause instanceof Error ? cause.message : String(cause),
    };
  }
}

/**
 * FEAT-UI-29 lifecycle adapter: it owns the widget configuration
 * lifecycle and the explicit invalid-configuration response. The widget
 * itself consumes no backend capability and has no transport states.
 */
export function NewsFeature({
  config: configInput,
}: NewsFeatureProps): React.JSX.Element {
  const { value: config, error: configError } = useMemo(
    () => resolveConfig(configInput),
    [configInput],
  );

  if (config === null) {
    return (
      <section
        role="alert"
        aria-label={`${NEWS_MANIFEST.title} configuration error`}
      >
        <h2>{NEWS_MANIFEST.title}</h2>
        <p>
          The widget configuration is invalid and was rejected instead of
          partially applied:
        </p>
        <pre>{configError}</pre>
      </section>
    );
  }

  return <NewsWidget defaultLanguage={config.defaultLanguage} />;
}
