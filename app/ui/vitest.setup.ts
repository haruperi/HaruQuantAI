import "@testing-library/jest-dom/vitest";

// jsdom does not implement ResizeObserver; dockview-core requires it whenever
// a real DockviewReact host mounts (tests that do not mock the module).
class ResizeObserverStub implements ResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;
}
