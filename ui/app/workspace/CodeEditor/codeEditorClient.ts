/**
 * Code Editor Workspace Client
 *
 * Connects the Code Editor IDE UI to the backend Python services:
 * - Document session tabs, atomic save, and syntax checking
 * - Virtual file system navigation, CRUD, clone, and search
 * - Python AST syntax compilation and dynamic reloading
 * - StrategyQuant X 12 snippet template generators
 * - Indicator tester with Lightweight Charts series
 * - Extension package export/import with collision resolution
 */

import { createDomainClient, type TransportConfig } from '../../host/transport';

export interface EditorTabDto {
  file_path: string;
  title: string;
  is_dirty: boolean;
  content: string;
  mode: string;
  cursor_position?: { line: number; column: number };
}

export interface WorkspaceInitDto {
  status: string;
  active_file: string | null;
  open_tabs: EditorTabDto[];
  layout: {
    navigator_visible: boolean;
    split_mode: string;
    bottom_panel: string;
  };
}

export interface NavigatorItemDto {
  id: string;
  name: string;
  type: 'file' | 'directory';
  extension?: string;
  path?: string;
  children?: NavigatorItemDto[];
}

export interface SyntaxDiagnosticDto {
  line: number;
  column: number;
  message: string;
  severity: 'error' | 'warning' | 'info';
  source_line?: string;
}

export interface CompileResultDto {
  file: string;
  timestamp: string;
  success: boolean;
  errors: SyntaxDiagnosticDto[];
  module_reloaded?: boolean;
}

export interface SnippetTemplateDto {
  template_id: string;
  name: string;
  description: string;
  category: string;
  default_filename: string;
  target_subdir: string;
}

export interface IndicatorTestCandlestick {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface IndicatorPlotPoint {
  time: number;
  value?: number;
}

export interface IndicatorTableRow {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  indicator_val: number | null;
  outputs?: Record<string, number | null>;
  reference_val?: number;
  diff?: number;
}

export interface IndicatorTestDiscrepancy {
  bar: number;
  time: number;
  calc: number;
  ref: number;
  diff: number;
}

export interface IndicatorTestResultDto {
  test_id: string;
  status: 'success' | 'failed';
  error?: string;
  symbol: string;
  timeframe: string;
  bars_calculated: number;
  candlesticks: IndicatorTestCandlestick[];
  indicator_plots: IndicatorPlotPoint[];
  plot_series?: Array<{ name: string; pane: string; data: IndicatorPlotPoint[] }>;
  table_rows: IndicatorTableRow[];
  discrepancies: IndicatorTestDiscrepancy[];
}

export interface ImportedFileRecord {
  filename: string;
  file_size: number;
  exists_locally: boolean;
}

export interface SearchMatchDto {
  file: string;
  line: number;
  column: number;
  text: string;
  match: string;
}

export function createCodeEditorClient(config: TransportConfig = {}) {
  const client = createDomainClient('/code-editor', config);

  return {
    async syncSession(tabs: EditorTabDto[], activeFile: string | null): Promise<WorkspaceInitDto> {
      return client.post('/session', { tabs, active_file: activeFile });
    },
    async saveTestConfig(testId: string, name: string): Promise<{ config_id: string }> {
      return client.post('/indicator-test/save', { test_id: testId, name });
    },
    async loadTestConfig(configId: string): Promise<{ config: Record<string, unknown> }> {
      return client.get(`/indicator-test/load?config_id=${encodeURIComponent(configId)}`);
    },
    async initWorkspace(): Promise<WorkspaceInitDto> {
      return client.get<WorkspaceInitDto>('/init');
    },

    async fetchNavigator(rootDir?: string): Promise<NavigatorItemDto> {
      const q = rootDir ? `?root_dir=${encodeURIComponent(rootDir)}` : '';
      return client.get<NavigatorItemDto>(`/navigator${q}`);
    },

    async fetchTabs(): Promise<EditorTabDto[]> {
      return client.get<EditorTabDto[]>('/tabs');
    },

    async openTab(filePath: string, mode = 'python'): Promise<{ status: string; tab: EditorTabDto; active_file: string }> {
      return client.post('/tabs/open', { file_path: filePath, mode });
    },

    async closeTab(filePath: string, force = false): Promise<{ status: string; closed_file?: string; active_file?: string | null }> {
      return client.post('/tabs/close', { file_path: filePath, force });
    },

    async saveFile(filePath: string, content: string): Promise<{ status: string; file_path: string; diagnostics: SyntaxDiagnosticDto[] }> {
      return client.post('/file/save', { file_path: filePath, content });
    },

    async saveAllFiles(files?: Array<{ file_path: string; content: string }>): Promise<{ status: string; count: number; files: unknown[] }> {
      return client.post('/file/save-all', { files });
    },

    async newFile(filePath: string, content = ''): Promise<{ status: string; file_path: string }> {
      return client.post('/file/new', { file_path: filePath, content });
    },

    async newDir(dirPath: string): Promise<{ status: string; dir_path: string }> {
      return client.post('/file/new-dir', { dir_path: dirPath });
    },

    async cloneFile(sourcePath: string, targetPath: string): Promise<{ status: string; file_path: string }> {
      return client.post('/file/clone', { source_path: sourcePath, target_path: targetPath });
    },

    async renameFile(oldPath: string, newPath: string): Promise<{ status: string; old_path: string; new_path: string }> {
      return client.post('/file/rename', { old_path: oldPath, new_path: newPath });
    },

    async deleteFile(filePath: string): Promise<{ status: string; file_path: string }> {
      return client.post('/file/delete', { file_path: filePath });
    },

    async searchFiles(
      query: string,
      options: { caseSensitive?: boolean; regex?: boolean; wholeWord?: boolean; searchDir?: string } = {}
    ): Promise<SearchMatchDto[]> {
      return client.post('/search', {
        query,
        case_sensitive: options.caseSensitive ?? false,
        regex: options.regex ?? false,
        whole_word: options.wholeWord ?? false,
        search_dir: options.searchDir,
      });
    },

    async compileFile(filePath: string, content?: string): Promise<CompileResultDto> {
      return client.post('/compile', { file_path: filePath, content });
    },

    async compileAll(): Promise<{ status: string; total_files: number; valid_files: number; results: CompileResultDto[] }> {
      return client.post('/compile-all', {});
    },

    async listTemplates(): Promise<SnippetTemplateDto[]> {
      return client.get<SnippetTemplateDto[]>('/templates');
    },

    async renderTemplatePreview(templateId: string, name: string): Promise<{ content: string; file_path: string }> {
      return client.post('/templates/render', { template_id: templateId, name });
    },

    async createFromTemplate(
      templateType: string,
      name: string,
      category = 'custom'
    ): Promise<{ status: string; template_type: string; name: string; file_path: string; tab: EditorTabDto }> {
      return client.post('/templates/create', { template_type: templateType, name, category });
    },

    async exportPack(
      filePaths: string[],
      archivePath: string,
      metadata?: Record<string, unknown>
    ): Promise<{ status: string; archive_path: string; file_count: number; files: string[] }> {
      return client.post('/import-export/export', { file_paths: filePaths, archive_path: archivePath, metadata });
    },

    async inspectPack(archivePath: string): Promise<ImportedFileRecord[]> {
      return client.post('/import-export/inspect', { archive_path: archivePath });
    },

    async importPack(
      archivePath: string,
      resolutionRules?: Record<string, string>
    ): Promise<{ status: string; extracted_count: number; skipped_count: number; extracted: string[]; skipped: string[] }> {
      return client.post('/import-export/import', { archive_path: archivePath, resolution_rules: resolutionRules });
    },

    async runIndicatorTest(params: {
      indicatorName: string;
      symbol?: string;
      timeframe?: string;
      params?: Record<string, unknown>;
      barsToReserve?: number;
      barCount?: number;
      referenceValues?: number[];
    }): Promise<IndicatorTestResultDto> {
      return client.post('/indicator-test/run', {
        indicator_name: params.indicatorName,
        symbol: params.symbol ?? 'EURUSD',
        timeframe: params.timeframe ?? 'H1',
        params: params.params ?? { period: 14 },
        bars_to_reserve: params.barsToReserve ?? 50,
        bar_count: params.barCount ?? 150,
        reference_values: params.referenceValues,
      });
    },

    async newIndicatorTest(indicatorName: string, symbol = 'EURUSD', timeframe = 'H1'): Promise<Record<string, unknown>> {
      return client.post('/indicator-test/new', { indicator_name: indicatorName, symbol, timeframe });
    },

    async editIndicatorParams(testId: string, params: Record<string, unknown>): Promise<IndicatorTestResultDto> {
      return client.post('/indicator-test/edit-params', { test_id: testId, params });
    },
  };
}
