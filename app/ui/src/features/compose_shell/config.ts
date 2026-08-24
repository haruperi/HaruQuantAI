/**
 * Strict configuration parser for FEAT-UI-COMPOSE_SHELL.
 */

export interface ComposeShellConfig {
  readonly defaultRoute: string;
  readonly showFooter: boolean;
  readonly title: string;
}

const ALLOWED_CONFIG_KEYS = new Set(["default_route", "show_footer", "title"]);

export function parseComposeShellConfig(
  raw?: Record<string, unknown>
): ComposeShellConfig {
  if (!raw) {
    return {
      defaultRoute: "/home",
      showFooter: true,
      title: "HaruQuantAI",
    };
  }

  const unknownKeys = Object.keys(raw).filter(
    (k) => !ALLOWED_CONFIG_KEYS.has(k)
  );
  if (unknownKeys.length > 0) {
    throw new Error(
      `Unknown configuration keys for ComposeShell: ${unknownKeys.sort().join(", ")}`
    );
  }

  const defaultRoute =
    typeof raw.default_route === "string" ? raw.default_route : "/home";
  const showFooter =
    typeof raw.show_footer === "boolean" ? raw.show_footer : true;
  const title = typeof raw.title === "string" ? raw.title : "HaruQuantAI";

  return {
    defaultRoute,
    showFooter,
    title,
  };
}
