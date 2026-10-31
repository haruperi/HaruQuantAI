/**
 * Code Editor Workspace Client
 *
 * Connects the Code Editor IDE UI to the backend Python services:
 * - Document session tabs, atomic save, and syntax checking
 * - Virtual file system navigation, CRUD, clone, and search
 * - Python AST syntax compilation and dynamic reloading
 * - StrategyQuant X 12 snippet template generators
 * - Indicator tester with Lightweight Charts series, batch suite, test distribution, and calibration
 * - Extension package export/import with interactive conflict resolution
 */

import { createDomainClient, type TransportConfig } from '../../shell/transport';

export interface EditorTabDto {
  file_path: string;
  title: string;
  is_dirty: boolean;
  content: string;
  mode: string;
  cursor_position?: { line: number; column: number };
}

export interface WorkspaceInitDto {
  recovery_warnings?: string[];
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
  protected?: boolean;
  ownership?: 'builtin' | 'user' | 'host';
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
  registered_classes?: string[];
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
  diff?: number | null;
}

export interface IndicatorDifference {
  bar: number;
  time: number;
  calc: number;
  ref: number;
  diff: number;
}

export interface IndicatorGapDiagnostic {
  bar: number;
  time: number;
  series: string;
  type: 'NonFiniteValue';
  message: string;
}

export interface IndicatorExecutionDiagnostic {
  bar: number;
  type: string;
  message: string;
}

export type IndicatorTestDiscrepancy =
  | IndicatorDifference
  | IndicatorGapDiagnostic
  | IndicatorExecutionDiagnostic;

export interface IndicatorConfigDto {
  test_id: string;
  indicator_name: string;
  symbol: string;
  timeframe: string;
  params: Record<string, unknown>;
  bars_to_reserve: number;
  bar_count: number;
  created_at?: number;
  reference_values?: number[] | null;
  saved_name?: string;
}

export interface SavedTestConfigDto {
  status: 'saved';
  config_id: string;
  config: IndicatorConfigDto;
}

export interface LoadedTestConfigDto {
  status: 'loaded';
  config: IndicatorConfigDto;
}

export interface SavedFileDto {
  file_path: string;
  diagnostics: SyntaxDiagnosticDto[];
}

export interface SaveFileResultDto extends SavedFileDto {
  status: 'saved';
  bytes_written: number;
}

export interface SaveAsResultDto extends SavedFileDto {
  status: 'saved_as';
  source_path: string;
  tab: EditorTabDto;
  active_file: string;
  bytes_written: number;
}

export interface ImportPackResultDto {
  status: 'completed';
  extracted_count: number;
  skipped_count: number;
  extracted: string[];
  skipped: string[];
  reload_results: CompileResultDto[];
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

export interface SymbolDto { name: string; module: string; file_path: string; kind: 'class' | 'function' | 'variable'; members: string[] }
export interface IndicatorDto { identity: string; name: string; file_path: string; outputs: string[]; parameters: Record<string, unknown>; protected: boolean }
export interface CompilationDto { job_id: string; status: string; progress: number; results: CompileResultDto[]; message: string; cancellation_requested: boolean; source_hashes?: Record<string, string> }
export interface RepairDto { content: string; added: string[]; unresolved: { symbol: string; candidates: string[] }[] }
export interface FormatDto { format_id: 'python' | 'pseudocode'; name: string; extension: string }
export interface PathInfoDto { file_path: string; ownership: 'builtin' | 'user' | 'host'; protected: boolean; exists: boolean; clone_target: string }
export interface SnippetOptions { indicator?: string; order_action_type?: string; mc_type?: string }

export interface SuiteIndicatorOptionDto {
  identity: string;
  indicator: string;
  class_name: string;
  output: string;
  file_path: string;
  default_parameters: string;
  parameters: Record<string, unknown>;
  protected: boolean;
}

export interface SuiteTestCaseDto {
  test_id: string;
  use: boolean;
  indicator: string;
  parameters: string;
  decimals: number;
  result: string;
  shift: number;
  file_name: string;
  exists: boolean;
  show_grid: boolean;
  errors: string[];
}

export interface SuiteConfigDto {
  engine: string;
  bars_to_reserve: number;
  tests: SuiteTestCaseDto[];
}

export interface SuiteSnapshotDto {
  job_id: string;
  status: 'IDLE' | 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'STOPPED' | 'FAILED' | 'INTERRUPTED';
  status_code: 0 | 1 | 3 | 4;
  progress: number;
  completed_tests: number;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  skipped_tests: number;
  cancellation_requested: boolean;
  message: string;
  config: SuiteConfigDto;
  xml_content: string;
}

export interface TestDistributionSnapshotDto {
  job_id: string;
  status: 'IDLE' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  progress: number;
  completed: boolean;
  error: string;
  installed_files: string[];
  config_updated: boolean;
}

export interface CalibrationRequestDto {
  project_name?: string;
  task_name?: string | null;
  symbols: string[];
  timeframes: string[];
  engine?: string;
  max_steps?: number;
  indicators?: string[];
  ranges_config_text?: string | null;
  bars_count?: number;
}

export interface CalibratedRangeEntryDto {
  key: string;
  indicator: string;
  output: string;
  min_value: number;
  max_value: number;
  step: number;
  mean: number;
  std_dev: number;
  samples: number;
}

export interface CalibrationResultDto {
  project_name: string;
  task_name?: string | null;
  engine: string;
  calibrated_count: number;
  skipped_indicators: string[];
  ranges: CalibratedRangeEntryDto[];
}

export interface SkippedImportItemDto {
  name: string;
  reason: string;
}

export interface ImportSessionSnapshotDto {
  session_id: string;
  status: 'RUNNING' | 'AWAITING_DECISION' | 'COMPLETED' | 'CANCELLED' | 'TIMED_OUT' | 'FAILED';
  decision_mode: 0 | 1 | 2 | 3 | 4 | 5;
  current_conflict: string | null;
  current_archive: string | null;
  processed_entries: number;
  total_entries: number;
  new_files: string[];
  not_imported_files: SkippedImportItemDto[];
  reload_results: CompileResultDto[];
  message: string;
}

export function createCodeEditorClient(config: TransportConfig = {}) {
  const client = createDomainClient('/code-editor', config);

  return {
    reloadDisk(filePath: string, discardDirty: boolean): Promise<{ tab: EditorTabDto; active_file: string }> {
      return client.post('/file/reload', { file_path: filePath, discard_dirty: discardDirty });
    },
    symbols(): Promise<SymbolDto[]> { return client.get('/catalogue/symbols'); },
    indicators(): Promise<IndicatorDto[]> { return client.get('/catalogue/indicators'); },
    pathInfo(filePath: string): Promise<PathInfoDto> { return client.get(`/file/info?file_path=${encodeURIComponent(filePath)}`); },
    repairImports(filePath: string, content: string, selections: Record<string, string> = {}): Promise<RepairDto> {
      return client.post('/imports/repair', { file_path: filePath, content, selections });
    },
    startCompilation(scope: 'file' | 'package' | 'all' | 'registered', filePath?: string, content?: string): Promise<CompilationDto> {
      return client.post('/compilations', { scope, file_path: filePath, content });
    },
    compilation(jobId?: string): Promise<CompilationDto | null> { return client.get(`/compilations${jobId ? `?job_id=${encodeURIComponent(jobId)}` : ''}`); },
    cancelCompilation(jobId: string): Promise<CompilationDto> { return client.post(`/compilations/${encodeURIComponent(jobId)}/cancel`, {}); },
    exportFormats(filePath?: string): Promise<FormatDto[]> { return client.get(`/export-formats${filePath ? `?file_path=${encodeURIComponent(filePath)}` : ''}`); },
    createExportTemplate(sourcePaths: string[], targetPath: string, formatId: string): Promise<SaveFileResultDto> {
      return client.post('/export-templates', { source_paths: sourcePaths, target_path: targetPath, format_id: formatId });
    },
    async syncSession(tabs: EditorTabDto[], activeFile: string | null): Promise<WorkspaceInitDto> {
      return client.post('/session', { tabs, active_file: activeFile });
    },
    async saveTestConfig(testId: string, name: string): Promise<SavedTestConfigDto> {
      return client.post('/indicator-test/save', { test_id: testId, name });
    },
    async loadTestConfig(configId: string): Promise<LoadedTestConfigDto> {
      return client.get(`/indicator-test/load?config_id=${encodeURIComponent(configId)}`);
    },
    async initWorkspace(): Promise<WorkspaceInitDto> {
      return client.get<WorkspaceInitDto>('/init');
    },

    async fetchNavigator(rootDir?: string, ownership = 'all'): Promise<NavigatorItemDto> {
      const params = [rootDir ? `root_dir=${encodeURIComponent(rootDir)}` : '', ownership !== 'all' ? `ownership=${ownership}` : ''].filter(Boolean);
      const q = params.length ? '?' + params.join('&') : '';
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

    async saveFile(filePath: string, content: string): Promise<SaveFileResultDto> {
      return client.post('/file/save', { file_path: filePath, content });
    },

    async saveAsFile(sourcePath: string, targetPath: string, content: string): Promise<SaveAsResultDto> {
      return client.post('/file/save-as', { source_path: sourcePath, target_path: targetPath, content });
    },

    async saveAllFiles(files?: Array<{ file_path: string; content: string }>): Promise<{ status: string; count: number; files: SavedFileDto[] }> {
      return client.post('/file/save-all', { files });
    },

    async newFile(filePath: string, content = ''): Promise<SaveFileResultDto> {
      return client.post('/file/new', { file_path: filePath, content });
    },

    async newDir(dirPath: string): Promise<{ status: string; dir_path: string }> {
      return client.post('/file/new-dir', { dir_path: dirPath });
    },

    async cloneFile(sourcePath: string, targetPath: string): Promise<SaveFileResultDto> {
      return client.post('/file/clone', { source_path: sourcePath, target_path: targetPath });
    },

    async renameFile(oldPath: string, newPath: string): Promise<{ status: string; old_path: string; new_path: string }> {
      return client.post('/file/rename', { old_path: oldPath, new_path: newPath });
    },

    async deleteFile(filePath: string): Promise<SaveFileResultDto> {
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

    async listTemplates(filePath?: string): Promise<SnippetTemplateDto[]> {
      return client.get<SnippetTemplateDto[]>(`/templates${filePath ? `?file_path=${encodeURIComponent(filePath)}` : ''}`);
    },

    async renderTemplatePreview(templateId: string, name: string, category?: string, options: SnippetOptions = {}): Promise<{ content: string; file_path: string }> {
      return client.post('/templates/render', { template_id: templateId, name, category, ...options });
    },

    async createFromTemplate(
      templateType: string,
      name: string,
      category = 'custom', options: SnippetOptions = {},
    ): Promise<{ status: string; template_type: string; name: string; file_path: string; tab: EditorTabDto }> {
      return client.post('/templates/create', { template_type: templateType, name, category, ...options });
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
    ): Promise<ImportPackResultDto> {
      return client.post('/import-export/import', { archive_path: archivePath, resolution_rules: resolutionRules });
    },

    async runIndicatorTest(params: {
      indicatorName: string;
      symbol?: string;
      timeframe?: string;
      params?: Record<string, unknown> | null;
      barsToReserve?: number;
      barCount?: number;
      referenceValues?: number[];
    }): Promise<IndicatorTestResultDto> {
      return client.post('/indicator-test/run', {
        indicator_name: params.indicatorName,
        symbol: params.symbol ?? 'EURUSD',
        timeframe: params.timeframe ?? 'H1',
        params: params.params ?? null,
        bars_to_reserve: params.barsToReserve ?? 50,
        bar_count: params.barCount ?? 150,
        reference_values: params.referenceValues,
      });
    },

    async newIndicatorTest(indicatorName: string, symbol = 'EURUSD', timeframe = 'H1'): Promise<IndicatorConfigDto> {
      return client.post('/indicator-test/new', { indicator_name: indicatorName, symbol, timeframe });
    },

    async editIndicatorParams(testId: string, params: Record<string, unknown>): Promise<IndicatorTestResultDto> {
      return client.post('/indicator-test/edit-params', { test_id: testId, params });
    },

    async suiteIndicators(): Promise<SuiteIndicatorOptionDto[]> {
      return client.get('/indicator-suite/indicators');
    },

    async suiteCreateConfig(
      indicators: string[] = [],
      engine = 'MetaTrader4',
      barsToReserve = 300
    ): Promise<SuiteSnapshotDto> {
      return client.post('/indicator-suite/config/new', {
        indicators,
        engine,
        bars_to_reserve: barsToReserve,
      });
    },

    async suiteAddTests(indicators: string[], allowDuplicates = false): Promise<SuiteSnapshotDto> {
      return client.post('/indicator-suite/config/add-tests', {
        indicators,
        allow_duplicates: allowDuplicates,
      });
    },

    async suiteGetConfig(): Promise<SuiteSnapshotDto> {
      return client.get('/indicator-suite/config');
    },

    async suiteLoadConfig(xmlContent?: string): Promise<SuiteSnapshotDto> {
      return client.post('/indicator-suite/config/load', { xml_content: xmlContent ?? null });
    },

    async suiteSaveConfig(payload: { config?: SuiteConfigDto; xml_content?: string }): Promise<SuiteSnapshotDto> {
      return client.post('/indicator-suite/config/save', payload);
    },

    async suiteStart(payload: { config?: SuiteConfigDto; selected_only?: boolean } = {}): Promise<SuiteSnapshotDto> {
      return client.post('/indicator-suite/start', {
        config: payload.config ?? null,
        selected_only: payload.selected_only ?? true,
      });
    },

    async suiteStop(jobId?: string): Promise<SuiteSnapshotDto> {
      const q = jobId ? `?job_id=${encodeURIComponent(jobId)}` : '';
      return client.post(`/indicator-suite/stop${q}`, {});
    },

    async suiteStatus(jobId?: string): Promise<SuiteSnapshotDto> {
      const q = jobId ? `?job_id=${encodeURIComponent(jobId)}` : '';
      return client.get(`/indicator-suite/status${q}`);
    },

    async downloadTests(payload: {
      archive_path?: string;
      source_url?: string;
      expected_sha256: string;
    }): Promise<TestDistributionSnapshotDto> {
      return client.post('/indicator-suite/download-tests', payload);
    },

    async downloadTestsStatus(jobId?: string): Promise<TestDistributionSnapshotDto> {
      const q = jobId ? `?job_id=${encodeURIComponent(jobId)}` : '';
      return client.get(`/indicator-suite/download-status${q}`);
    },

    async calibrateIndicators(payload: CalibrationRequestDto): Promise<CalibrationResultDto> {
      return client.post('/indicator-suite/calibrate', payload);
    },

    async listExportableFiles(filterText = ''): Promise<NavigatorItemDto> {
      const q = filterText ? `?filter_text=${encodeURIComponent(filterText)}` : '';
      return client.get(`/import-export/list${q}`);
    },

    async startImportSession(
      archivePaths: string[],
      timeoutSeconds = 60
    ): Promise<ImportSessionSnapshotDto> {
      return client.post('/import-export/session/start', {
        archive_paths: archivePaths,
        timeout_seconds: timeoutSeconds,
      });
    },

    async getImportSession(sessionId?: string): Promise<ImportSessionSnapshotDto> {
      const q = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
      return client.get(`/import-export/session${q}`);
    },

    async applyImportSessionAction(
      sessionId: string,
      action: 'overwrite' | 'overwrite_always' | 'skip' | 'skip_always' | 'cancel'
    ): Promise<ImportSessionSnapshotDto> {
      return client.post('/import-export/session/action', { session_id: sessionId, action });
    },
  };
}
