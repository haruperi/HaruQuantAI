import { reservedDarwinex, useDarwinex } from '../../Darwinex/darwinexStore';
import { reservedCrypto, useCrypto } from '../../Crypto/cryptoStore';
import { reservedYahoo, useYahoo } from '../../Yahoo/yahooStore';
import { reservedMt5, useMt5Import } from '../../MetaTrader/mt5ImportStore';
import { datasets } from '../../Common/fixtures';
import { useDataManagerStore, useDukascopyDownloads, useTickDownloader } from '../../Common/dataManagerStore';
import { useFileSymbols } from '../../FileImport/fileSymbolsStore';
import { activeImport, useFileImports } from '../../FileImport/fileImportStore';
import { lookupSQ, type SQConfig } from '../sqData';
import { useSQData } from '../sqDataStore';
import { useAppStore } from '../../../../host/store';
export const futuresService = {
  lookup: (config: SQConfig) => lookupSQ('futures', config),
  start(config: SQConfig, selected: string[], agreed: boolean): void {
      const data = useDataManagerStore.getState(), td = useTickDownloader.getState(), files = useFileSymbols.getState(), imports = useFileImports.getState();
      if (data.storageError || td.storageError || files.storageError || imports.storageError) throw new Error(data.storageError || td.storageError || files.storageError || imports.storageError);
      const existing = [...reservedYahoo(), ...reservedCrypto(), ...reservedDarwinex(), ...reservedMt5(), ...datasets, ...data.definitions, ...td.definitions, ...files.definitions, ...imports.records, ...(activeImport(imports.job?.state) ? imports.job!.tasks.map(task => task.record) : [])];
      useSQData.getState().start('futures', config, selected, agreed, useAppStore.getState().settings.profile, existing.map(row => row.symbol), [useYahoo.getState().job?.state, useCrypto.getState().job?.state, useDarwinex.getState().job?.state, useMt5Import.getState().job?.state, td.job?.state, useDukascopyDownloads.getState().job?.state, imports.job?.state].some(activeImport));
  },
  update(dispatch: (label: string) => void): void { dispatch('Futures dataset update'); },
};
