/** Explicit registration lifecycle for the FEAT-UI-TYPED_BACKEND capability. */

import { ApiClientError } from "./request";
import { TypedBackendLifecycle } from "./lifecycle";
import {
  TYPED_BACKEND_CAPABILITY,
  TYPED_BACKEND_MANIFEST,
} from "./manifest";

/** Concrete removable typed-backend contribution. */
export class TypedBackendFeature {
  public readonly manifest = TYPED_BACKEND_MANIFEST;

  public constructor(
    public readonly lifecycle: TypedBackendLifecycle = new TypedBackendLifecycle(),
  ) {}

  /** Dispose all feature-owned effects. */
  public async dispose(): Promise<void> {
    await this.lifecycle.dispose();
  }
}

/** Minimal exact-key registry used by composition without provider fallback. */
export class TypedBackendCapabilityRegistry {
  private readonly entries = new Map<string, unknown>();

  /** Register any exact capability, rejecting an existing provider. */
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

  /** Resolve FEAT-UI-TYPED_BACKEND or fail with an explicit unavailable outcome. */
  public requireTypedBackend(): TypedBackendFeature {
    const feature = this.resolve<TypedBackendFeature>(TYPED_BACKEND_CAPABILITY);
    if (!feature) {
      throw new ApiClientError({
        message: "typed backend capability is unavailable",
        status: 0,
        code: "DEPENDENCY_UNAVAILABLE",
      });
    }
    return feature;
  }

  /** Register FEAT-UI-TYPED_BACKEND and return an async exact-generation disposer. */
  public registerTypedBackend(feature: TypedBackendFeature): () => Promise<void> {
    const unregister = this.register(TYPED_BACKEND_CAPABILITY, feature);
    let active = true;
    return async () => {
      if (!active) return;
      active = false;
      unregister();
      await feature.dispose();
    };
  }
}
