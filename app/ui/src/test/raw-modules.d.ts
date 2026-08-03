/**
 * Ambient declaration for vitest `?raw` imports used in contract tests.
 *
 * vitest (via vite) supports `import x from './module?raw'` to load the source
 * text; TypeScript needs this ambient module declaration to type-check it.
 */

declare module "*?raw" {
  const source: string;
  export default source;
}
