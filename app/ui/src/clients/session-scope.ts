/** Global browser-session scope fence for FEAT-UI-SESSION_ACCESS. */

let controller = new AbortController();
let generation = 0;

/** Return the current session-scope abort signal. */
export function currentSessionScopeSignal(): AbortSignal {
  return controller.signal;
}

/** Return the current monotonically increasing session-scope generation. */
export function currentSessionScopeGeneration(): number {
  return generation;
}

/** Abort all work tied to the previous principal/account scope and advance generation. */
export function rotateSessionScope(reason = "session-scope-changed"): number {
  controller.abort(reason);
  controller = new AbortController();
  generation += 1;
  return generation;
}
