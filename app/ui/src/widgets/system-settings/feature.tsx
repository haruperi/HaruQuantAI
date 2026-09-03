"use client";

import { useMemo } from "react";

import {
  resolveSystemSettingsConfig,
  type SystemSettingsConfig,
} from "./config";
import { SYSTEM_SETTINGS_MANIFEST } from "./manifest";
import { SystemSettingsModal } from "./SystemSettingsModal";

/** Props for the FEAT-UI-13 lifecycle adapter. */
export interface SystemSettingsFeatureProps {
  /**
   * Raw widget configuration (strict schema); `undefined` selects the
   * documented defaults and invalid input renders an explicit
   * configuration-error state instead of silently passing through.
   */
  readonly config?: unknown;
}

interface ResolvedConfig {
  readonly value: SystemSettingsConfig | null;
  readonly error: string | null;
}

function resolveConfig(input: unknown | undefined): ResolvedConfig {
  try {
    return { value: resolveSystemSettingsConfig(input), error: null };
  } catch (cause) {
    return {
      value: null,
      error: cause instanceof Error ? cause.message : String(cause),
    };
  }
}

/**
 * FEAT-UI-13 lifecycle adapter: it owns the widget configuration
 * lifecycle and the explicit invalid-configuration response; `SystemSettingsModal`
 * remains focused presentation.
 */
export function SystemSettingsFeature({
  config: configInput,
}: SystemSettingsFeatureProps): React.JSX.Element {
  const { value: config, error: configError } = useMemo(
    () => resolveConfig(configInput),
    [configInput],
  );

  if (config === null) {
    return (
      <section
        role="alert"
        aria-label={`${SYSTEM_SETTINGS_MANIFEST.title} configuration error`}
      >
        <h2>{SYSTEM_SETTINGS_MANIFEST.title}</h2>
        <p>
          The widget configuration is invalid and was rejected instead of
          partially applied:
        </p>
        <pre>{configError}</pre>
      </section>
    );
  }

  return <SystemSettingsModal />;
}
