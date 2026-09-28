/** Explicit resource transport and a separately labelled local preview cache.
 * Preview snapshots are UI fixtures, never authoritative research publications.
 */
import { createDomainClient } from './transport';
import type { ResourceBytes, ResourceRef } from './resourceContracts';

export const resourceClient = {
  list: (): Promise<ResourceRef[]> => createDomainClient('/resources').get('/'),
  read: (reference: ResourceRef): Promise<ResourceBytes> => createDomainClient('/resources').post('/read', reference),
};

type PreviewDocument = { readonly revision: number; readonly json: string };
type Listener = (document: PreviewDocument) => void;

/** An injected host-owned cache exchanges inert documents, never feature functions. */
export class PreviewResources {
  private readonly documents = new Map<string, PreviewDocument>();
  private readonly listeners = new Map<string, Set<Listener>>();

  read(id: string, initial: unknown): PreviewDocument {
    const saved = this.documents.get(id);
    if (saved) return saved;
    const raw = typeof localStorage === 'undefined' ? null : localStorage.getItem('host.preview.resource.' + id);
    const stored: unknown = raw === null ? null : JSON.parse(raw);
    if (stored !== null && (typeof stored !== 'object' || !('revision' in stored) || !Number.isInteger(stored.revision) || !('json' in stored) || typeof stored.json !== 'string')) throw new Error('Invalid saved preview resource; stored data is retained');
    const document = Object.freeze(stored === null ? { revision: 1, json: JSON.stringify(initial) } : stored as PreviewDocument);
    JSON.parse(document.json);
    if (typeof localStorage !== 'undefined') localStorage.setItem('host.preview.resource.' + id, JSON.stringify(document));
    this.documents.set(id, document);
    return document;
  }

  publish(id: string, value: unknown, expectedRevision: number): PreviewDocument {
    const previous = this.documents.get(id);
    if (previous && previous.revision !== expectedRevision) throw new Error('Preview resource revision conflict');
    const json = JSON.stringify(value);
    if (previous?.json === json) return previous;
    const document = Object.freeze({ revision: (previous?.revision ?? 0) + 1, json });
    if (typeof localStorage !== 'undefined') localStorage.setItem('host.preview.resource.' + id, JSON.stringify(document));
    this.documents.set(id, document);
    for (const listener of this.listeners.get(id) ?? []) listener(document);
    return document;
  }

  subscribe(id: string, listener: Listener): () => void {
    const listeners = this.listeners.get(id) ?? new Set<Listener>();
    listeners.add(listener);
    this.listeners.set(id, listeners);
    return () => { listeners.delete(listener); if (!listeners.size) this.listeners.delete(id); };
  }

  clear(): void {
    this.documents.clear();
    this.listeners.clear();
  }
}

// This host cache contains only inert prototype documents. It is not a provider
// registry and must never be used to infer backend execution availability.
export const previewResources = new PreviewResources();

/** Preserve legacy local view data without importing another owner's store. */
export const ownerViewStorage = {
  getItem: (name: string): string | null => localStorage.getItem(name) ?? localStorage.getItem('sqx-recreation-v1'),
  setItem: (name: string, value: string): void => { localStorage.setItem(name, value); },
  removeItem: (name: string): void => { localStorage.removeItem(name); },
};

/** Merge only declared view fields; persisted functions/unknown fields never win. */
export function mergeViewState<T extends object>(saved: unknown, current: T): T {
  if (!saved || typeof saved !== 'object' || Array.isArray(saved)) return current;
  const result = { ...current };
  for (const key of Object.keys(current) as (keyof T)[]) {
    if (typeof current[key] === 'function' || !(key in saved)) continue;
    const value = (saved as Partial<T>)[key];
    const previous = current[key];
    result[key] = (value && previous && typeof value === 'object' && typeof previous === 'object' &&
      !Array.isArray(value) && !Array.isArray(previous) ? { ...previous, ...value } : value) as T[keyof T];
  }
  return result;
}

export function connectPreviewDocument<S extends object, K extends keyof S>(
  store: { getState(): S; setState(patch: Partial<S>): void; subscribe(listener: (state: S) => void): () => void },
  field: K,
  resourceId: string,
  resources: PreviewResources,
): () => void {
  let latest = resources.read(resourceId, store.getState()[field]);
  let applying = false;
  const accept = (document: PreviewDocument) => {
    latest = document;
    applying = true;
    try { store.setState({ [field]: JSON.parse(document.json) } as Partial<S>); }
    finally { applying = false; }
  };
  accept(latest);
  const removeListener = resources.subscribe(resourceId, accept);
  const removeStore = store.subscribe(state => {
    if (!applying) latest = resources.publish(resourceId, state[field], latest.revision);
  });
  return () => { removeListener(); removeStore(); };
}
