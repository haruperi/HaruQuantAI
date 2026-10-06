import { useDataManagerStore, useDukascopyDownloads } from '../Common/dataManagerStore';
import type { AddDukasRequest } from './dukascopy';
import type { DownloadRequest } from './dukascopyDownload';

/** Typed adapters to the retained local mock stores; no live provider calls. */
export function useDukascopyAddService() {
  const brokers = useDataManagerStore((state) => state.brokers);
  const storageError = useDataManagerStore((state) => state.storageError);
  const add = useDataManagerStore((state) => state.addData);
  return { brokers, storageError, addData: (request: AddDukasRequest): void => add(request) };
}

export function useDukascopyDownloadService() {
  const preferred = useDukascopyDownloads((state) => state.preferred);
  const begin = useDukascopyDownloads((state) => state.start);
  return { preferred, start: (request: DownloadRequest): void => begin(request) };
}
