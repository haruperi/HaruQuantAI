import { filesService } from '../FileImport/DataSourceFilesService';
import { emptyFileRecord } from '../FileImport/fileImport';
import { newSymbol } from '../FileImport/fileSymbols';
import { discoverTD, type TDRequest } from './tickDownloader';
import { useTickDownloader } from '../Common/dataManagerStore';
/** Adapter to existing metadata discovery and shared mock persistence. */
export const tdService = {
  loadAvailableSymbols: discoverTD,
  async importData(request: TDRequest, available: string[], files: File[] = []): Promise<void> {
    if (!request.symbols.length || request.symbols.some(symbol=>!available.includes(symbol))) throw new Error('Select symbols from the chosen folder.');
    const tasks = files.flatMap(file=>{const symbol=request.symbols.find(name=>(file.webkitRelativePath || file.name).toUpperCase().includes(name.toUpperCase())); return symbol && /\.(csv|txt|tsv|hst|fxt|dat|parquet|gz|zip)$/i.test(file.name) ? [{file,filename:file.name,provider:'tickdownloader',ignored:0,record:{...emptyFileRecord(symbol+request.postfix,newSymbol(),'start'),underlying:symbol,timeframe:'auto',timestamps:[],unknownBars:0}}] : [];});
    await filesService.start(tasks,'UTC','',0);
  },
  importDataAction(action: 'pause' | 'resume' | 'stop'): void { useTickDownloader.getState().action(action); },
};
