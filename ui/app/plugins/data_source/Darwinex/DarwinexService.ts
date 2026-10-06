import { datasets } from '../Common/fixtures';
import { useDataManagerStore, useDukascopyDownloads, useTickDownloader } from '../Common/dataManagerStore';
import { useFileSymbols } from '../FileImport/fileSymbolsStore';
import { useFileImports } from '../FileImport/fileImportStore';
import { reservedSQDefinitions, useSQData } from '../SQData/sqDataStore';
import { darwinexActive, reservedDarwinex, useDarwinex } from './darwinexStore';
import { reservedCrypto, useCrypto } from '../Crypto/cryptoStore';
import { reservedYahoo, useYahoo } from '../Yahoo/yahooStore';
import { reservedMt5, useMt5Import } from '../MetaTrader/mt5ImportStore';
import { darwinexCatalogue, darwinexDefinitions, discoverDarwinex, type DarwinexDefinition, type DarwinexDownload } from './darwinex';
import { useAppStore } from '../../../host/store';

export function darwinexContext(): { existing: string[]; active: boolean } {
  const data = useDataManagerStore.getState(), td = useTickDownloader.getState(), files = useFileSymbols.getState(), imports = useFileImports.getState();
  const error = data.storageError || td.storageError || files.storageError || imports.storageError;
  if (error) throw new Error(error);
  const rows = [...datasets, ...data.definitions, ...td.definitions, ...files.definitions, ...imports.records, ...reservedCrypto(), ...reservedYahoo(), ...reservedSQDefinitions(), ...reservedDarwinex(), ...reservedMt5(), ...(darwinexActive(imports.job?.state) ? imports.job!.tasks.map(task => task.record) : [])];
  return { existing: rows.map(row => row.symbol), active: [td.job?.state, imports.job?.state, useSQData.getState().job?.state, useMt5Import.getState().job?.state, useDukascopyDownloads.getState().job?.state, useCrypto.getState().job?.state, useYahoo.getState().job?.state].some(darwinexActive) };
}
export const darwinexService = {
  catalogue: darwinexCatalogue,
  definitions: darwinexDefinitions,
  discover: discoverDarwinex,
  context: darwinexContext,
  start(kind: 'add' | 'import', definitions: DarwinexDefinition[], active: boolean, folder?: string, postfix?: string): void {
    useDarwinex.getState().start(kind, definitions, active, folder, postfix);
  },
  download(request: DarwinexDownload): void {
    useDarwinex.getState().download(request, useAppStore.getState().settings.profile === 'Full', darwinexContext().active);
  },
};
