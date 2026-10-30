import { useAppStore } from '../../../../shell/store';
import { useDatabankStore } from './databankStore';
/** Attach the mapped pane to existing application and view-store authorities. */
export function useDatabankContext() {
  return { store: useAppStore(), databankStore: useDatabankStore() };
}
