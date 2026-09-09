/** Explicit registration lifecycle for the FEAT-UI-SESSION_ACCESS capability. */

import { ApiClientError } from "@/clients";

import { SessionAccessLifecycle } from "./lifecycle";
import {
  SESSION_ACCESS_CAPABILITY,
  SESSION_ACCESS_MANIFEST,
} from "./manifest";

/** Concrete removable access-gate contribution. */
export class SessionAccessFeature {
  public readonly manifest = SESSION_ACCESS_MANIFEST;

  public constructor(
    public readonly lifecycle: SessionAccessLifecycle =
      new SessionAccessLifecycle(),
  ) {}

  /** Dispose all feature-owned effects. */
  public async dispose(): Promise<void> {
    await this.lifecycle.dispose();
  }
}

/** Minimal exact-key registry used by UI composition without fallback. */
export class SessionAccessCapabilityRegistry {
  private readonly entries = new Map<string, unknown>();

  /** Register one exact capability, rejecting an existing provider. */
  public register<T>(capability: string, provider: T): () => void {
    if (this.entries.has(capability)) {
      throw new ApiClientError({
        message: `capability already registered: ${capability}`,
        status: 0,
        code: "IDEMPOTENCY_CONFLICT",
      });
    }
    this.entries.set(capability, provider);
    let active = true;
    return () => {
      if (!active) return;
      active = false;
      if (this.entries.get(capability) === provider) {
        this.entries.delete(capability);
      }
    };
  }

  /** Resolve one exact capability without scanning for substitutes. */
  public resolve<T>(capability: string): T | undefined {
    return this.entries.get(capability) as T | undefined;
  }

  /** Resolve the access gate or fail with an explicit unavailable outcome. */
  public requireSessionAccess(): SessionAccessFeature {
    const feature = this.resolve<SessionAccessFeature>(
      SESSION_ACCESS_CAPABILITY,
    );
    if (!feature) {
      throw new ApiClientError({
        message: "session access capability is unavailable",
        status: 0,
        code: "DEPENDENCY_UNAVAILABLE",
      });
    }
    return feature;
  }

  /** Register and return an idempotent exact-generation disposer. */
  public registerSessionAccess(
    feature: SessionAccessFeature,
  ): () => Promise<void> {
    const unregister = this.register(SESSION_ACCESS_CAPABILITY, feature);
    let active = true;
    return async () => {
      if (!active) return;
      active = false;
      unregister();
      await feature.dispose();
    };
  }
}
