/** Lifecycle and physical-removal acceptance for FEAT-UI-SESSION_ACCESS. */

import { describe, expect, it, vi } from "vitest";

import { SessionAccessCapabilityRegistry, SessionAccessFeature } from "../feature";
import { SessionAccessLifecycle } from "../lifecycle";
import { SESSION_ACCESS_MANIFEST } from "../manifest";

const scope = {
  principalId: "user-a",
  accountId: "account-a",
  workspaceId: "workspace-a",
} as const;

describe("FEAT-UI-SESSION_ACCESS lifecycle", () => {
  it("test_trc_present_session_access_nfr_001", async () => {
    const lifecycle = new SessionAccessLifecycle();
    const selection = { value: "source-object-17" };
    const retainedSource = Object.freeze({ id: selection.value });
    const clear = vi.fn(() => {
      selection.value = "";
    });
    const active = await lifecycle.transition(scope);
    expect(active.scope).toEqual(scope);
    expect(active.signal.aborted).toBe(false);
    const unregisterProjection = lifecycle.registerProjection(
      "workspace.selection",
      clear,
    );

    await lifecycle.transition(null);
    expect(active.signal.aborted).toBe(true);
    expect(clear).toHaveBeenCalledTimes(1);
    expect(selection.value).toBe("");
    expect(retainedSource).toEqual({ id: "source-object-17" });
    unregisterProjection();
    unregisterProjection();

    const registry = new SessionAccessCapabilityRegistry();
    const unrelated = Object.freeze({ capability: "ui.unrelated@1" });
    registry.register("ui.unrelated@1", unrelated);
    const feature = new SessionAccessFeature(lifecycle);
    const withdraw = registry.registerSessionAccess(feature);
    expect(feature.manifest).toBe(SESSION_ACCESS_MANIFEST);
    expect(registry.requireSessionAccess()).toBe(feature);

    await withdraw();
    await withdraw();
    expect(() => registry.requireSessionAccess()).toThrowError(
      expect.objectContaining({ code: "DEPENDENCY_UNAVAILABLE" }),
    );
    expect(registry.resolve("ui.unrelated@1")).toBe(unrelated);
    expect(feature.lifecycle.isDisposed).toBe(true);
    await expect(feature.lifecycle.transition(scope)).rejects.toMatchObject({
      code: "DEPENDENCY_UNAVAILABLE",
    });
  });

  it("bounds projection registrations and rejects duplicate ownership", () => {
    const lifecycle = new SessionAccessLifecycle();
    const unregister = lifecycle.registerProjection("one", () => undefined);
    expect(() =>
      lifecycle.registerProjection("one", () => undefined),
    ).toThrowError(expect.objectContaining({ code: "IDEMPOTENCY_CONFLICT" }));
    expect(() =>
      lifecycle.registerProjection("contains payload", () => undefined),
    ).toThrowError(expect.objectContaining({ code: "VALIDATION_FAILED" }));
    unregister();
  });

  it("awaits a consumer-released async projection before publishing a new scope", async () => {
    const lifecycle = new SessionAccessLifecycle();
    await lifecycle.transition(scope);
    let release: (() => void) | undefined;
    const clear = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          release = resolve;
        }),
    );
    const unregister = lifecycle.registerProjection("consumer.cache", clear);
    unregister();
    unregister();

    const nextScope = { ...scope, accountId: "account-b" };
    let settled = false;
    const transition = lifecycle.transition(nextScope).then((snapshot) => {
      settled = true;
      return snapshot;
    });
    await Promise.resolve();
    expect(clear).toHaveBeenCalledTimes(1);
    expect(settled).toBe(false);

    release?.();
    await expect(transition).resolves.toMatchObject({ scope: nextScope });
    await lifecycle.dispose();
  });
});
