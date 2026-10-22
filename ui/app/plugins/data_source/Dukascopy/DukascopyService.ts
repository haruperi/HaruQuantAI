import { useDataManagerStore, useDukascopyDownloads } from '../Common/dataManagerStore';
import type { AddDukasRequest } from './dukascopy';
import type { DownloadRequest } from './dukascopyDownload';

/** Shared host-backed registration/catalog adapters and simulated downloads. */
export function useDukascopyAddService() {
  const brokers = useDataManagerStore((state) => state.brokers);
  const brokerLoading = useDataManagerStore((state) => state.brokerLoading);
  const brokerError = useDataManagerStore((state) => state.brokerError);
  const reloadBrokers = useDataManagerStore((state) => state.syncBrokers);
  const add = useDataManagerStore((state) => state.addData);
  return { brokers, brokerLoading, brokerError, reloadBrokers, addData: (request: AddDukasRequest): Promise<void> => add(request) };
}

export function useDukascopyDownloadService() {
  const preferred = useDukascopyDownloads((state) => state.preferred);
  const begin = useDukascopyDownloads((state) => state.start);
  return { preferred, start: (request: DownloadRequest): void => begin(request) };
}
