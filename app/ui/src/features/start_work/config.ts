/**
 * Strict configuration parser for FEAT-UI-START_WORK.
 *
 * `default_route` follows README §5: Home (`/home`) is used only when the
 * start-work feature is installed and authorized; otherwise the caller falls
 * back to a deterministic diagnostic route.
 */

export interface StartWorkConfig {
  readonly defaultRoute: string;
  readonly newsEnabled: boolean;
}

const ALLOWED_CONFIG_KEYS = new Set(["default_route", "news_enabled"]);

export function parseStartWorkConfig(
  raw?: Record<string, unknown>
): StartWorkConfig {
  if (!raw) {
    return {
      defaultRoute: "/home",
      newsEnabled: true,
    };
  }

  const unknownKeys = Object.keys(raw).filter(
    (k) => !ALLOWED_CONFIG_KEYS.has(k)
  );
  if (unknownKeys.length > 0) {
    throw new Error(
      `Unknown configuration keys for StartWork: ${unknownKeys.sort().join(", ")}`
    );
  }

  const defaultRoute =
    typeof raw.default_route === "string" ? raw.default_route : "/home";
  const newsEnabled =
    typeof raw.news_enabled === "boolean" ? raw.news_enabled : true;

  return {
    defaultRoute,
    newsEnabled,
  };
}
