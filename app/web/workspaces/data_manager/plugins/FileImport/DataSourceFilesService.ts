import { useSymbols } from '../Catalogs/Symbols/symbolsStore';
import { saveRemoteSymbol, toFileSymbol } from '../Catalogs/Symbols/symbolsApiClient';
import { sourceClient, refreshSourceCatalog } from '../Common/historicalSourceStore';
import { reservedDarwinex, useDarwinex } from '../Darwinex/darwinexStore';
import { reservedCrypto, useCrypto } from '../Crypto/cryptoStore';
import { reservedYahoo, useYahoo } from '../Yahoo/yahooStore';
import { reservedSQDefinitions, useSQData } from '../SQData/sqDataStore';
import { reservedMt5, useMt5Import } from '../MetaTrader/mt5ImportStore';
import { datasets } from '../Common/fixtures';
import { useDataManagerStore, useDukascopyDownloads } from '../Common/dataManagerStore';
import { activeImport, useFileImports } from './fileImportStore';
import { useFileSymbols } from './fileSymbolsStore';
import { readImportFile, type ImportTask, type ImportRecord, type ImportFormat } from './fileImport';
import type { FileSymbol, FileDefinition } from './fileSymbols';

export const filesService = {
  read: readImportFile,
  massContext(records: ImportRecord[]): { id: string; symbol: string; source: string }[] {
    const data = useDataManagerStore.getState(), symbols = useFileSymbols.getState();
    if (data.storageError || symbols.storageError) throw new Error(data.storageError || symbols.storageError);
    const existing = [...reservedYahoo(), ...reservedCrypto(), ...reservedDarwinex(), ...reservedSQDefinitions(), ...reservedMt5(), ...datasets, ...data.definitions, ...symbols.definitions, ...records];
    return existing;
  },
  async start(tasks: ImportTask[], timezone: string, group: string, skipped: number): Promise<void> {
    await useFileImports.getState().start(tasks, timezone, group, skipped, [useYahoo.getState().job?.state, useCrypto.getState().job?.state, useDarwinex.getState().job?.state, useSQData.getState().job?.state, useMt5Import.getState().job?.state, useDukascopyDownloads.getState().job?.state].some(activeImport));
  },
  async addSymbolDefinition(value: FileSymbol, brokerIds: string[]): Promise<FileSymbol> {
    const saved = {...value,...toFileSymbol(await saveRemoteSymbol(value, value.brokerName || 'File'))};
    await useSymbols.getState().refreshFromServer();
    useFileSymbols.getState().addSymbolDefinition(saved,brokerIds);
    return saved;
  },
  async addSymbol(symbol: string, symbolDefinition: FileSymbol, barType: 'start' | 'end', existing: string[]): Promise<void> {
    await sourceClient.post('/datasets/create',{source:'files',symbol,underlying:symbolDefinition.symbol,timeframe:'M1',broker:symbolDefinition.brokerName,category:symbolDefinition.type,tick_size:symbolDefinition.tickSize,symbol_definition_id:symbolDefinition.id ? Number(symbolDefinition.id) : undefined,exchange:symbolDefinition.exchange,expiry:symbolDefinition.expiry});
    await refreshSourceCatalog();
  },
  saveFormat(format: ImportFormat, replace?: boolean): void {
    useFileImports.getState().saveFormat(format, replace);
  },
  deleteFormat(name: string): void {
    useFileImports.getState().deleteFormat(name);
  },
};
