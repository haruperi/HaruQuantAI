/** Browser metadata equivalent of TD directory discovery; never reads file contents. */
export interface TDManifest { folder: string; symbols: string[]; fileCount: number }
export interface TDRequest { folder: string; symbols: string[]; postfix: string }
export interface TDJob { request: TDRequest; state: 'running' | 'paused' | 'completed' | 'cancelled' | 'failed'; progress: number; error?: string }
export function discoverTD(paths: string[]): TDManifest {
  if (!paths.length) throw new Error('No symbols available. Select a folder containing downloaded data.');
  if (paths.length > 20000) throw new Error('Select a folder with at most 20,000 files in this selection.');
  const parts = paths.map(path => {
    const segments = path.split('/');
    if (path.length > 1024 || segments.some(part => !part || part === '.' || part === '..' || /[\\:\x00-\x1f]/.test(part))) throw new Error('Invalid folder structure.');
    return segments;
  });
  const folder = parts[0][0];
  if (parts.some(path => path[0] !== folder)) throw new Error('Select one installation folder.');
  // SQX uses installation/tickdata when present, otherwise the selected directory.
  const nested = parts.some(path => path[1]?.toLowerCase() === 'tickdata' && path.length >= 3);
  const symbols = [...new Set(parts.filter(path => nested ? path[1]?.toLowerCase() === 'tickdata' && path.length >= 4 : path.length >= 3).map(path => path[nested ? 2 : 1]))];
  if (symbols.length > 1000) throw new Error('Select at most 1,000 symbol folders.');
  return { folder, symbols, fileCount: paths.length };
}
export function validateTD(request: TDRequest, available: string[], existing: string[]): void {
  if (!request.folder || request.folder.length > 255 || /[\\/\x00-\x1f]/.test(request.folder)) throw new Error('Select a TickDownloader installation folder.');
  if (!request.symbols.length) throw new Error('Select at least one symbol.');
  if (request.symbols.length > 1000 || request.postfix.length > 64 || /[\\/\x00-\x1f]/.test(request.postfix)) throw new Error('Invalid postfix or symbol count.');
  const names = new Set(existing);
  for (const symbol of request.symbols) {
    if (!available.includes(symbol)) throw new Error('Select symbols from the chosen folder.');
    if (names.has(symbol + request.postfix)) throw new Error(`Symbol with name '${symbol + request.postfix}' already exists. Please enter a postfix to generate unique symbol names.`);
    names.add(symbol + request.postfix);
  }
}
