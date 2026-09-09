/** Bounded offline executable usage for FEAT-UI-SESSION_ACCESS. */

import assert from "node:assert/strict";

import { SessionAccessCapabilityRegistry, SessionAccessFeature } from "./feature";
import { SessionAccessLifecycle } from "./lifecycle";

async function main(): Promise<void> {
  const lifecycle = new SessionAccessLifecycle();
  const projection = { selectedResourceId: "fixture-resource" };

  const accountA = await lifecycle.transition({
    principalId: "usage-user-a",
    accountId: "usage-account-a",
    workspaceId: "usage-workspace-a",
  });
  assert.equal(accountA.signal.aborted, false);
  assert.equal(lifecycle.isCurrent(accountA.generation), true);
  const releaseProjection = lifecycle.registerProjection(
    "usage.selection",
    async () => {
      await Promise.resolve();
      projection.selectedResourceId = "";
    },
  );
  releaseProjection();
  releaseProjection();

  const accountB = await lifecycle.transition({
    principalId: "usage-user-b",
    accountId: "usage-account-b",
    workspaceId: "usage-workspace-b",
  });
  assert.equal(accountA.signal.aborted, true);
  assert.equal(lifecycle.isCurrent(accountA.generation), false);
  assert.equal(lifecycle.isCurrent(accountB.generation), true);
  assert.equal(projection.selectedResourceId, "");

  const registry = new SessionAccessCapabilityRegistry();
  const unrelated = Object.freeze({ state: "retained" });
  registry.register("ui.unrelated@1", unrelated);
  const feature = new SessionAccessFeature(lifecycle);
  const withdraw = registry.registerSessionAccess(feature);
  assert.equal(registry.requireSessionAccess(), feature);
  await withdraw();
  await assert.rejects(async () => registry.requireSessionAccess(), {
    code: "DEPENDENCY_UNAVAILABLE",
  });
  assert.equal(registry.resolve("ui.unrelated@1"), unrelated);

  console.log(
    "FEAT-UI-SESSION_ACCESS usage passed: verified scope, account transition, stale abort, projection cleanup, exact withdrawal, and unrelated-state retention proved offline.",
  );
}

await main();
