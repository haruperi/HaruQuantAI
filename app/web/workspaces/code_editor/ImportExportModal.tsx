import React, { useEffect, useRef, useState } from 'react';
import {
  Download,
  FileCode,
  Folder,
  FolderArchive,
  Upload,
  X,
} from 'lucide-react';
import {
  createCodeEditorClient,
  type ImportedFileRecord,
  type ImportSessionSnapshotDto,
  type NavigatorItemDto,
} from './codeEditorClient';

interface ImportExportModalProps {
  onClose: () => void;
  openFiles?: string[];
  onImportComplete?: () => void;
}

function flattenFiles(node: NavigatorItemDto | null): string[] {
  if (!node) return [];
  if (node.type === 'file' && node.path) return [node.path];
  return (node.children ?? []).flatMap((child) => flattenFiles(child));
}

export function ImportExportModal({ onClose, openFiles = [], onImportComplete }: ImportExportModalProps) {
  const client = createCodeEditorClient();

  // Export state
  const [packName, setPackName] = useState<string>('MySnippetPack');
  const [description, setDescription] = useState<string>(
    'Custom indicator and strategy extension pack including snippets.'
  );
  const [outputFilePath, setOutputFilePath] = useState<string>('app/include/my_pack.zip');
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [exportFilter, setExportFilter] = useState<string>('');
  const [userExportFiles, setUserExportFiles] = useState<string[] | null>(null);

  // Import state
  const [importFilePath, setImportFilePath] = useState<string>('app/include/my_pack.zip');
  const [importOption, setImportOption] = useState<'merge' | 'overwrite' | 'rename'>('overwrite');
  const [isInspecting, setIsInspecting] = useState<boolean>(false);
  const [isImporting, setIsImporting] = useState<boolean>(false);
  const [importPreview, setImportPreview] = useState<ImportedFileRecord[]>([]);
  const [importMessage, setImportMessage] = useState<string | null>(null);
  const [inspectedArchive, setInspectedArchive] = useState<string | null>(null);
  const [sessionSnapshot, setSessionSnapshot] = useState<ImportSessionSnapshotDto | null>(null);
  const inspectionRevision = useRef(0);
  const canImport =
    importPreview.length > 0 &&
    inspectedArchive === importFilePath.trim() &&
    !isInspecting &&
    !isImporting;

  useEffect(() => () => { inspectionRevision.current++; }, []);

  const handleArchiveChange = (path: string) => {
    inspectionRevision.current++;
    setImportFilePath(path);
    setImportPreview([]);
    setInspectedArchive(null);
    setImportMessage(null);
    setSessionSnapshot(null);
    setIsInspecting(false);
  };

  const handleLoadUserSnippets = async () => {
    try {
      const tree = await client.listExportableFiles(exportFilter.trim());
      setUserExportFiles(flattenFiles(tree));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to list user snippets';
      setExportMessage(`Error: ${msg}`);
    }
  };

  const handleExport = async () => {
    const targetFiles = userExportFiles && userExportFiles.length > 0 ? userExportFiles : openFiles;
    if (!targetFiles.length || isExporting) return;
    setIsExporting(true);
    setExportMessage(null);
    try {
      const res = await client.exportPack(targetFiles, outputFilePath, {
        name: packName,
        description,
      });
      setExportMessage(`Successfully exported ${res.file_count} file(s) to ${res.archive_path}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Export failed';
      setExportMessage(`Error: ${msg}`);
    } finally {
      setIsExporting(false);
    }
  };

  const handleInspect = async () => {
    const archive = importFilePath.trim();
    if (!archive || isInspecting || isImporting) return;
    const revision = ++inspectionRevision.current;
    setIsInspecting(true);
    setImportMessage(null);
    setImportPreview([]);
    setInspectedArchive(null);
    try {
      const files = await client.inspectPack(archive);
      if (revision !== inspectionRevision.current) return;
      setImportPreview(files);
      setInspectedArchive(archive);
      if (files.length === 0) {
        setImportMessage('Archive is empty or does not contain snippets.');
      }
    } catch (err: unknown) {
      if (revision !== inspectionRevision.current) return;
      const msg = err instanceof Error ? err.message : 'Inspection failed';
      setImportMessage(`Error: ${msg}`);
    } finally {
      if (revision === inspectionRevision.current) setIsInspecting(false);
    }
  };

  const handleImport = async () => {
    if (!canImport || inspectedArchive === null) return;
    setIsImporting(true);
    setImportMessage(null);
    try {
      const resolutionRules: Record<string, string> = {};
      importPreview.forEach((file) => {
        resolutionRules[file.filename] = importOption === 'merge' ? 'skip' : importOption;
      });
      const res = await client.importPack(inspectedArchive, resolutionRules);
      setImportMessage(
        `Import complete: ${res.extracted_count} extracted, ${res.skipped_count} skipped.`
      );
      if (onImportComplete) onImportComplete();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Import failed';
      setImportMessage(`Error: ${msg}`);
    } finally {
      setIsImporting(false);
    }
  };

  const handleStartInteractiveSession = async () => {
    const archive = importFilePath.trim();
    if (!archive || isImporting) return;
    setIsImporting(true);
    setImportMessage(null);
    try {
      const snap = await client.startImportSession([archive]);
      setSessionSnapshot(snap);
      if (snap.status === 'COMPLETED') {
        setImportMessage(snap.message);
        if (onImportComplete) onImportComplete();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Interactive import failed';
      setImportMessage(`Error: ${msg}`);
    } finally {
      setIsImporting(false);
    }
  };

  const handleSessionAction = async (
    action: 'overwrite' | 'overwrite_always' | 'skip' | 'skip_always' | 'cancel'
  ) => {
    if (!sessionSnapshot) return;
    setIsImporting(true);
    try {
      const snap = await client.applyImportSessionAction(sessionSnapshot.session_id, action);
      setSessionSnapshot(snap);
      if (snap.status !== 'AWAITING_DECISION') {
        setImportMessage(snap.message);
        if (snap.new_files.length > 0 && onImportComplete) {
          onImportComplete();
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Conflict decision failed';
      setImportMessage(`Error: ${msg}`);
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-5xl h-[88vh] max-h-[820px] rounded-xl border border-slate-700/80 bg-slate-900 text-slate-100 shadow-2xl flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <FolderArchive className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
                Import / Export Extension Pack
              </h2>
              <p className="text-xs text-slate-400">
                Package and share your Python snippets.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 hover:bg-slate-800 p-1.5 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body - 2 Columns */}
        <div className="flex-1 grid grid-cols-2 divide-x divide-slate-800 overflow-hidden bg-slate-950/40">
          {/* Left Column: Export Pack */}
          <div className="p-6 flex flex-col justify-between overflow-y-auto space-y-4">
            <div className="space-y-4">
              <div className="flex items-center gap-2.5 pb-2 border-b border-slate-800">
                <div className="p-2 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30">
                  <Upload className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Export Pack</h3>
                  <p className="text-[11px] text-slate-400">
                    Create a distributable pack from your open Python snippets.
                  </p>
                </div>
              </div>

              <div>
                <label htmlFor="pack-name" className="block text-xs font-medium text-slate-300 mb-1">
                  Pack Name
                </label>
                <input
                  id="pack-name"
                  type="text"
                  value={packName}
                  onChange={(e) => setPackName(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
                />
              </div>

              <div>
                <label htmlFor="pack-description" className="block text-xs font-medium text-slate-300 mb-1">
                  Description
                </label>
                <textarea
                  id="pack-description"
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>

              <p className="text-xs text-slate-400">
                Export uses saved files on disk. Save changes before exporting; unsaved buffers are not included.
                Each pack includes the source files and a manifest with its name and description.
              </p>
              {!openFiles.length && !userExportFiles?.length && (
                <p className="text-xs text-amber-300">Open a Python snippet to export.</p>
              )}

              <div>
                <label htmlFor="pack-output" className="block text-xs font-medium text-slate-300 mb-1">
                  Output File
                </label>
                <div className="relative">
                  <input
                    id="pack-output"
                    type="text"
                    value={outputFilePath}
                    onChange={(e) => setOutputFilePath(e.target.value)}
                    className="w-full pl-3 pr-8 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 font-mono"
                  />
                  <Folder className="w-4 h-4 text-slate-400 absolute right-2.5 top-2" />
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800/80 space-y-2">
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    aria-label="User snippet filter"
                    placeholder="Filter user snippets..."
                    value={exportFilter}
                    onChange={(e) => setExportFilter(e.target.value)}
                    className="flex-1 px-2.5 py-1 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => void handleLoadUserSnippets()}
                    className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700"
                  >
                    Filter User Snippets
                  </button>
                </div>
                {userExportFiles && (
                  <div className="text-[11px] text-slate-300 font-mono max-h-24 overflow-y-auto space-y-0.5">
                    {userExportFiles.map((f) => (
                      <div key={f}>{f}</div>
                    ))}
                  </div>
                )}
              </div>

              {exportMessage && (
                <div className="text-xs p-2.5 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-300">
                  {exportMessage}
                </div>
              )}
            </div>

            <div className="pt-4 flex items-center justify-end gap-2 border-t border-slate-800/80">
              <button
                onClick={handleExport}
                disabled={isExporting || (!openFiles.length && !userExportFiles?.length)}
                className="px-4 py-1.5 text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white rounded-lg flex items-center gap-1.5 transition-colors disabled:opacity-50"
              >
                <Upload className="w-3.5 h-3.5" />
                {isExporting ? 'Exporting...' : 'Export Pack'}
              </button>
            </div>
          </div>

          {/* Right Column: Import Pack */}
          <div className="p-6 flex flex-col justify-between overflow-y-auto space-y-4">
            <div className="space-y-4">
              <div className="flex items-center gap-2.5 pb-2 border-b border-slate-800">
                <div className="p-2 rounded-lg bg-emerald-600/20 text-emerald-400 border border-emerald-500/30">
                  <Download className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Import Pack</h3>
                  <p className="text-[11px] text-slate-400">Import an extension pack into your workspace.</p>
                </div>
              </div>

              <div>
                <label htmlFor="pack-import" className="block text-xs font-medium text-slate-300 mb-1">
                  Select Pack File
                </label>
                <div className="flex items-center gap-2">
                  <input
                    id="pack-import"
                    type="text"
                    value={importFilePath}
                    onChange={(e) => handleArchiveChange(e.target.value)}
                    disabled={isImporting}
                    className="flex-1 px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 font-mono"
                  />
                  <button
                    onClick={handleInspect}
                    disabled={isInspecting || isImporting || !importFilePath.trim()}
                    className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors border border-slate-700"
                  >
                    {isInspecting ? 'Inspecting...' : 'Inspect'}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Import Options</label>
                <div className="space-y-1.5 text-xs">
                  <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                    <input
                      type="radio"
                      name="importOption"
                      checked={importOption === 'merge'}
                      onChange={() => setImportOption('merge')}
                      className="text-blue-600"
                    />
                    <span>Merge with existing files (Keep existing files)</span>
                  </label>
                  <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                    <input
                      type="radio"
                      name="importOption"
                      checked={importOption === 'overwrite'}
                      onChange={() => setImportOption('overwrite')}
                      className="text-blue-600"
                    />
                    <span>Overwrite existing files (Replace existing with pack contents)</span>
                  </label>
                  <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                    <input
                      type="radio"
                      name="importOption"
                      checked={importOption === 'rename'}
                      onChange={() => setImportOption('rename')}
                      className="text-blue-600"
                    />
                    <span>Import with rename (Save duplicates with _imported suffix)</span>
                  </label>
                </div>
              </div>

              <p className="text-xs text-slate-400">
                Archive-relative paths determine import destinations within the authorized snippet roots.
                Inspect the selected archive before importing.
              </p>

              {/* Package contents preview */}
              {importPreview.length > 0 && (
                <div className="rounded-lg border border-slate-800 bg-slate-950 p-2 max-h-40 overflow-y-auto">
                  <div className="text-[11px] font-medium text-slate-400 mb-1.5">
                    Package Contents ({importPreview.length} files)
                  </div>
                  <div className="space-y-1">
                    {importPreview.map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between text-[11px] py-0.5 px-1 font-mono">
                        <span className="flex items-center gap-1.5 text-slate-300 truncate">
                          <FileCode className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                          <span className="truncate">{item.filename}</span>
                        </span>
                        <span
                          className={`text-[10px] px-1.5 py-0.2 rounded font-sans ${
                            item.exists_locally
                              ? 'bg-amber-500/20 text-amber-300'
                              : 'bg-emerald-500/20 text-emerald-300'
                          }`}
                        >
                          {item.exists_locally ? 'Overwrite' : 'New'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Interactive Conflict Resolution Panel */}
              {sessionSnapshot && sessionSnapshot.status === 'AWAITING_DECISION' && (
                <div
                  role="region"
                  aria-label="Interactive Conflict Resolution"
                  className="rounded-lg border border-amber-500/40 bg-amber-950/20 p-3 space-y-2 text-xs"
                >
                  <div className="font-semibold text-amber-300">
                    Conflict Detected: <span className="font-mono">{sessionSnapshot.current_conflict}</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    <button
                      type="button"
                      onClick={() => void handleSessionAction('overwrite')}
                      className="px-2.5 py-1 bg-amber-600 hover:bg-amber-500 text-white rounded text-xs"
                    >
                      Overwrite
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleSessionAction('overwrite_always')}
                      className="px-2.5 py-1 bg-amber-700 hover:bg-amber-600 text-white rounded text-xs"
                    >
                      Overwrite All
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleSessionAction('skip')}
                      className="px-2.5 py-1 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded text-xs"
                    >
                      Skip
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleSessionAction('skip_always')}
                      className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs"
                    >
                      Skip All
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleSessionAction('cancel')}
                      className="px-2.5 py-1 bg-rose-700 hover:bg-rose-600 text-white rounded text-xs"
                    >
                      Cancel Session
                    </button>
                  </div>
                </div>
              )}

              {sessionSnapshot && sessionSnapshot.not_imported_files.length > 0 && (
                <div className="rounded-lg border border-slate-800 bg-slate-950 p-2 text-[11px] font-mono space-y-1 max-h-28 overflow-y-auto">
                  <div className="font-sans font-semibold text-slate-400">
                    Not Imported ({sessionSnapshot.not_imported_files.length}):
                  </div>
                  {sessionSnapshot.not_imported_files.map((item, idx) => (
                    <div key={idx} className="text-amber-300">
                      {item.name}: {item.reason}
                    </div>
                  ))}
                </div>
              )}

              {importMessage && (
                <div className="text-xs p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                  {importMessage}
                </div>
              )}
            </div>

            <div className="pt-4 flex items-center justify-end gap-2 border-t border-slate-800/80">
              <button
                type="button"
                onClick={() => void handleStartInteractiveSession()}
                disabled={isImporting || !importFilePath.trim()}
                className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 transition-colors disabled:opacity-50"
              >
                Interactive Import
              </button>
              <button
                onClick={handleImport}
                disabled={!canImport}
                className="px-4 py-1.5 text-xs font-medium bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg flex items-center gap-1.5 transition-colors disabled:opacity-50"
              >
                <Download className="w-3.5 h-3.5" />
                {isImporting ? 'Importing...' : 'Import Pack'}
              </button>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="border-t border-slate-800 px-6 py-3 bg-slate-900/90 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium text-slate-300 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors border border-slate-700/80"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
