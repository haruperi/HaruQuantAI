import { datasets } from '../Common/fixtures';
import { reservedCrypto, useCrypto } from '../Crypto/cryptoStore';
import { useDataManagerStore, useDukascopyDownloads, useTickDownloader } from '../Common/dataManagerStore';
import { reservedDarwinex, useDarwinex } from '../Darwinex/darwinexStore';
import { activeImport, useFileImports } from '../FileImport/fileImportStore';
import { useFileSymbols } from '../FileImport/fileSymbolsStore';
import { reservedSQDefinitions, useSQData } from '../SQData/sqDataStore';
import { yahooDefinitions, type YahooDownload } from './yahoo';
import { reservedYahoo, useYahoo, yahooActive } from './yahooStore';
import { reservedMt5, useMt5Import } from '../MetaTrader/mt5ImportStore';

export function yahooContext(): { existing: string[]; active: boolean } {
  const data = useDataManagerStore.getState(), td = useTickDownloader.getState(), files = useFileSymbols.getState(), imports = useFileImports.getState(), yahoo = useYahoo.getState();
  const error = data.storageError || td.storageError || files.storageError || imports.storageError || yahoo.storageError;
  if (error) throw new Error(error);
  const rows = [...datasets, ...data.definitions, ...td.definitions, ...files.definitions, ...imports.records, ...reservedSQDefinitions(), ...reservedDarwinex(), ...reservedCrypto(), ...reservedYahoo(), ...reservedMt5(), ...(activeImport(imports.job?.state) ? imports.job!.tasks.map(task => task.record) : [])];
  const active = [td.job?.state, imports.job?.state, useSQData.getState().job?.state, useMt5Import.getState().job?.state, useDukascopyDownloads.getState().job?.state, useDarwinex.getState().job?.state, useCrypto.getState().job?.state].some(yahooActive);
  return { existing: rows.map(row => row.symbol), active };
}

/** Attach independent UI workflows to existing mock persistence authority. */
export const yahooService = {
  add(symbols: string, postfix: string): void { const context = yahooContext(); useYahoo.getState().startAdd(yahooDefinitions(symbols, postfix, context.existing), context.active); },
  importData(request: YahooDownload): void { useYahoo.getState().startDownload(request, yahooContext().active); },
  importDataAction(action: 'pause' | 'resume' | 'stop'): void { useYahoo.getState().action(action); },
};
