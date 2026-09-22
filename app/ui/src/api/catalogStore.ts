/**
 * Reactive client-side store for catalog caching and graph draft recovery.
 */

import { defaultApiClient, type HaruApiClient } from './client';
import type {
  CatalogEntryView,
  CatalogView,
  GraphDocument,
  OperationSpec,
} from './contracts.generated';

export interface CatalogStoreState {
  catalog: CatalogView | null;
  loading: boolean;
  error: string | null;
  drafts: Record<string, GraphDocument>;
}

type Listener = (state: CatalogStoreState) => void;

export class CatalogStore {
  private state: CatalogStoreState = {
    catalog: null,
    loading: false,
    error: null,
    drafts: {},
  };

  private listeners: Set<Listener> = new Set();
  private client: HaruApiClient;

  constructor(client: HaruApiClient = defaultApiClient) {
    this.client = client;
    this.loadDraftsFromStorage();
  }

  getState(): CatalogStoreState {
    return this.state;
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private emit(): void {
    for (const listener of this.listeners) {
      listener(this.state);
    }
  }

  async fetchCatalog(): Promise<CatalogView> {
    this.state = { ...this.state, loading: true, error: null };
    this.emit();

    try {
      const catalog = await this.client.getCatalog();
      this.state = { ...this.state, catalog, loading: false };
      this.emit();
      return catalog;
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      this.state = { ...this.state, loading: false, error: errorMsg };
      this.emit();
      throw err;
    }
  }

  getEntry(pluginRefString: string): CatalogEntryView | undefined {
    return this.state.catalog?.entries.find(
      (e) => e.ref === pluginRefString || e.ref.startsWith(`${pluginRefString}@`),
    );
  }

  getOperation(
    pluginRefString: string,
    operationId: string,
  ): OperationSpec | undefined {
    const entry = this.getEntry(pluginRefString);
    return entry?.operations.find((op) => op.operation_id === operationId);
  }

  isPluginAvailable(pluginRefString: string): boolean {
    return this.getEntry(pluginRefString) !== undefined;
  }

  saveDraft(id: string, doc: GraphDocument): void {
    this.state = {
      ...this.state,
      drafts: { ...this.state.drafts, [id]: doc },
    };
    this.emit();
    this.persistDraftsToStorage();
  }

  getDraft(id: string): GraphDocument | undefined {
    return this.state.drafts[id];
  }

  listDrafts(): string[] {
    return Object.keys(this.state.drafts);
  }

  deleteDraft(id: string): void {
    const updated = { ...this.state.drafts };
    delete updated[id];
    this.state = { ...this.state, drafts: updated };
    this.emit();
    this.persistDraftsToStorage();
  }

  private loadDraftsFromStorage(): void {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const raw = window.localStorage.getItem('haru_graph_drafts_v1');
        if (raw) {
          this.state.drafts = JSON.parse(raw);
        }
      }
    } catch {
      // Storage unavailable in test/SSR
    }
  }

  private persistDraftsToStorage(): void {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(
          'haru_graph_drafts_v1',
          JSON.stringify(this.state.drafts),
        );
      }
    } catch {
      // Storage unavailable in test/SSR
    }
  }
}

export const defaultCatalogStore = new CatalogStore();
