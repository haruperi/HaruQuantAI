import { datasets } from '../Common/fixtures';
import { cryptoDefinitions, cryptoExchange, type CryptoExchangeId, type CryptoDefinition, type CryptoDownload } from './crypto';
import { cryptoActive, reservedCrypto, useCrypto } from './cryptoStore';
import { useDataManagerStore, useDukascopyDownloads, useTickDownloader } from '../Common/dataManagerStore';
import { reservedDarwinex, useDarwinex } from '../Darwinex/darwinexStore';
import { activeImport, useFileImports } from '../FileImport/fileImportStore';
import { useFileSymbols } from '../FileImport/fileSymbolsStore';
import { reservedSQDefinitions, useSQData } from '../SQData/sqDataStore';
import { reservedYahoo, useYahoo } from '../Yahoo/yahooStore';
import { reservedMt5, useMt5Import } from '../MetaTrader/mt5ImportStore';

export function cryptoContext(): { existing: string[]; active: boolean } {
  const data = useDataManagerStore.getState(), td = useTickDownloader.getState(), files = useFileSymbols.getState(), imports = useFileImports.getState();
  const error = data.storageError || td.storageError || files.storageError || imports.storageError || useCrypto.getState().storageError || useYahoo.getState().storageError;
  if (error) throw new Error(error);
  const rows = [...datasets, ...data.definitions, ...td.definitions, ...files.definitions, ...imports.records, ...reservedSQDefinitions(), ...reservedDarwinex(), ...reservedCrypto(), ...reservedYahoo(), ...reservedMt5(), ...(activeImport(imports.job?.state) ? imports.job!.tasks.map(task => task.record) : [])];
  const active = [td.job?.state, imports.job?.state, useSQData.getState().job?.state, useMt5Import.getState().job?.state, useDukascopyDownloads.getState().job?.state, useDarwinex.getState().job?.state, useYahoo.getState().job?.state].some(cryptoActive);
  return { existing: rows.map(row => row.symbol), active };
}

export const cryptoService = {
  exchange: cryptoExchange,
  add(exchangeId: CryptoExchangeId, selected: string[], timeframe: string, postfix: string): void {
    const context = cryptoContext();
    const definitions: CryptoDefinition[] = cryptoDefinitions(exchangeId, selected, timeframe, postfix, context.existing);
    useCrypto.getState().startAdd(definitions, context.active);
  },
  download(request: CryptoDownload): void {
    useCrypto.getState().startDownload(request, cryptoContext().active);
  },
};
