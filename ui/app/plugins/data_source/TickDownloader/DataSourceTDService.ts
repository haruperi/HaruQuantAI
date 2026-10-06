import { discoverTD, type TDRequest } from './tickDownloader';
import { useTickDownloader } from '../Common/dataManagerStore';
/** Adapter to existing metadata discovery and shared mock persistence. */
export const tdService = {
  loadAvailableSymbols: discoverTD,
  importData(request: TDRequest, available: string[]): void { useTickDownloader.getState().start(request, available); },
  importDataAction(action: 'pause' | 'resume' | 'stop'): void { useTickDownloader.getState().action(action); },
};
