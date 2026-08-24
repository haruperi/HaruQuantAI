import React from "react";
import type { UiFeatureInstance } from "../../runtime/composition_bridge";
import { SPEC } from "./manifest";
import { parseComposeShellConfig, type ComposeShellConfig } from "./config";
import { Shell } from "./Shell";

export class ComposeShellFeature implements UiFeatureInstance {
  public readonly manifest = SPEC;
  public readonly config: ComposeShellConfig;

  constructor(config?: Record<string, unknown>) {
    this.config = parseComposeShellConfig(config);
  }

  public render(headerSlot?: React.ReactNode, footerSlot?: React.ReactNode): React.ReactNode {
    return (
      <Shell
        title={this.config.title}
        showFooter={this.config.showFooter}
        headerSlot={headerSlot}
        footerSlot={footerSlot}
      />
    );
  }
}

export function createFeature(config?: Record<string, unknown>): ComposeShellFeature {
  return new ComposeShellFeature(config);
}
