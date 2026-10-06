import { reservedDarwinex, useDarwinex } from '../Darwinex/darwinexStore';
import { reservedCrypto, useCrypto } from '../Crypto/cryptoStore';
import { reservedYahoo, useYahoo } from '../Yahoo/yahooStore';
import { reservedSQDefinitions, useSQData } from '../SQData/sqDataStore';
import { reservedMt5, useMt5Import } from '../MetaTrader/mt5ImportStore';
import { datasets } from '../Common/fixtures';
import { useDataManagerStore, useDukascopyDownloads, useTickDownloader } from '../Common/dataManagerStore';
import { activeImport, useFileImports } from './fileImportStore';
import { useFileSymbols } from './fileSymbolsStore';
import { readImportFile, type ImportTask, type ImportRecord, type ImportFormat } from './fileImport';
import type { FileInstrument, FileDefinition } from './fileSymbols';

export const filesService = {
  read: readImportFile,
  massContext(records: ImportRecord[]): { id: string; symbol: string; source: string }[] {
    const data = useDataManagerStore.getState(), td = useTickDownloader.getState(), symbols = useFileSymbols.getState();
    if (data.storageError || td.storageError || symbols.storageError) throw new Error(data.storageError || td.storageError || symbols.storageError);
    const existing = [...reservedYahoo(), ...reservedCrypto(), ...reservedDarwinex(), ...reservedSQDefinitions(), ...reservedMt5(), ...datasets, ...data.definitions, ...td.definitions, ...symbols.definitions, ...records];
    return existing;
  },
  start(tasks: ImportTask[], timezone: string, group: string, skipped: number): void {
    useFileImports.getState().start(tasks, timezone, group, skipped, [useYahoo.getState().job?.state, useCrypto.getState().job?.state, useDarwinex.getState().job?.state, useSQData.getState().job?.state, useMt5Import.getState().job?.state, useDukascopyDownloads.getState().job?.state, useTickDownloader.getState().job?.state].some(activeImport));
  },
  addInstrument(value: FileInstrument, brokerIds: string[]): void {
    useFileSymbols.getState().addInstrument(value, brokerIds);
  },
  addSymbol(symbol: string, instrument: FileInstrument, barType: 'start' | 'end', existing: string[]): void {
    useFileSymbols.getState().addSymbol(symbol, instrument, barType, existing);
  },
  saveFormat(format: ImportFormat, replace?: boolean): void {
    useFileImports.getState().saveFormat(format, replace);
  },
  deleteFormat(name: string): void {
    useFileImports.getState().deleteFormat(name);
  },
};
