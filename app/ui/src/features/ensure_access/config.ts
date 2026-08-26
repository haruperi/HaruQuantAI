/**
 * Strict configuration parser for FEAT-UI-ENSURE_ACCESS.
 * Rejects every unknown configuration key.
 */

export interface EnsureAccessConfig {
  readonly schemaVersion: 1;
}

export function parseEnsureAccessConfig(
  raw?: Record<string, unknown>
): EnsureAccessConfig {
  if (!raw) {
    return {
      schemaVersion: 1,
    };
  }

  const unknownKeys = Object.keys(raw);
  if (unknownKeys.length > 0) {
    throw new Error(
      `Unknown configuration keys for EnsureAccess: ${unknownKeys.sort().join(", ")}`
    );
  }

  return {
    schemaVersion: 1,
  };
}
