import { datasets } from '../Common/fixtures';
import { reservedCrypto, useCrypto } from '../Crypto/cryptoStore';
import { useDataManagerStore, useDukascopyDownloads, useTickDownloader } from '../Common/dataManagerStore';
import { reservedDarwinex, useDarwinex } from '../Darwinex/darwinexStore';
import { activeImport, useFileImports } from '../FileImport/fileImportStore';
import { useFileSymbols } from '../FileImport/fileSymbolsStore';
import { discoverMt5Folder, filterMt5Symbols, mt5Definitions, mt5Symbols, type Mt5ImportRequest } from './mt5Import';
import { mt5Active, reservedMt5, useMt5Import } from './mt5ImportStore';
import { reservedSQDefinitions, useSQData } from '../SQData/sqDataStore';
import { reservedYahoo, useYahoo } from '../Yahoo/yahooStore';

export function mt5Context(): { existing: string[]; active: boolean } {
  const data = useDataManagerStore.getState();
  const td = useTickDownloader.getState();
  const files = useFileSymbols.getState();
  const imports = useFileImports.getState();
  const mt5 = useMt5Import.getState();
  const error = data.storageError || td.storageError || files.storageError || imports.storageError || mt5.storageError;
  if (error) throw new Error(error);
  const rows = [...datasets, ...data.definitions, ...td.definitions, ...files.definitions, ...imports.records,
    ...reservedSQDefinitions(), ...reservedDarwinex(), ...reservedCrypto(), ...reservedYahoo(), ...reservedMt5(),
    ...(activeImport(imports.job?.state) ? imports.job!.tasks.map(task => task.record) : [])];
  const active = [td.job?.state, imports.job?.state, useSQData.getState().job?.state,
    useDukascopyDownloads.getState().job?.state, useDarwinex.getState().job?.state,
    useCrypto.getState().job?.state, useYahoo.getState().job?.state].some(mt5Active);
  return { existing: rows.map(row => row.symbol), active };
}

export const mt5Api = {
  discover: discoverMt5Folder,
  filter: filterMt5Symbols,
  symbols: mt5Symbols,
  start(request: Mt5ImportRequest): void {
    const context = mt5Context();
    useMt5Import.getState().start(request, mt5Definitions(request, context.existing), context.active);
  },
};
