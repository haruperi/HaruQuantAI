"use client";

import React, { useMemo } from "react";

import { resolveCollectionGridConfig, type CollectionGridConfig } from "./config";
import { CollectionGrid, type CollectionGridProps } from "./CollectionGrid";
import { COLLECTION_GRID_MANIFEST } from "./manifest";

export interface CollectionGridFeatureProps<T = Record<string, unknown>>
  extends Partial<Omit<CollectionGridProps<T>, "config">> {
  readonly config?: unknown;
}

interface ResolvedConfig {
  readonly value: CollectionGridConfig | null;
  readonly error: string | null;
}

function resolveConfig(input: unknown | undefined): ResolvedConfig {
  try {
    return { value: resolveCollectionGridConfig(input), error: null };
  } catch (cause) {
    return {
      value: null,
      error: cause instanceof Error ? cause.message : String(cause),
    };
  }
}

/**
 * FEAT-UI-VIEW_COLLECTIONS lifecycle adapter:
 * Validates configuration and handles explicit configuration error fallback.
 */
export function CollectionGridFeature<T = Record<string, unknown>>({
  config: configInput,
  columns = [],
  rows = [],
  ...restProps
}: CollectionGridFeatureProps<T>): React.JSX.Element {
  const { value: config, error: configError } = useMemo(
    () => resolveConfig(configInput),
    [configInput],
  );

  if (config === null) {
    return (
      <section
        role="alert"
        aria-label={`${COLLECTION_GRID_MANIFEST.title} configuration error`}
      >
        <h2>{COLLECTION_GRID_MANIFEST.title}</h2>
        <p>
          The widget configuration is invalid and was rejected instead of
          partially applied:
        </p>
        <pre>{configError}</pre>
      </section>
    );
  }

  return (
    <CollectionGrid<T>
      columns={columns}
      rows={rows}
      config={config}
      {...restProps}
    />
  );
}
