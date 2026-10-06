import { useDatabankStore, type DatabankStoreState } from '../ProjectDatabanks/databankStore';

/** Attach view editing to the existing store and persistence authority. */
export function useDatabankViewsService(): DatabankStoreState {
  return useDatabankStore();
}
