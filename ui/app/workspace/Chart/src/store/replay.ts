export const replayStep = (index: number, delta: number, length: number) =>
  Math.max(0, Math.min(length - 1, index + delta));
