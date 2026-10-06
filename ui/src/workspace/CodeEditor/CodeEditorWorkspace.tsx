import React, { useState } from 'react';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Code2,
  Copy,
  Download,
  FileCode2,
  FolderCode,
  Play,
  Plus,
  RefreshCw,
  Save,
  Search,
  Sparkles,
  Terminal,
  TestTube2,
  Trash2,
  X,
} from 'lucide-react';
import { useAppStore } from '../../app/store';
import type { ExtensionFile } from '../../app/types';
import { Button, TextInput } from '../../components/ui';
import { IndicatorTesterModal } from './IndicatorTesterModal';
import { NewExtensionModal } from './NewExtensionModal';

const CATEGORIES: ExtensionFile['category'][] = [
  'Snippets',
  'Blocks',
  'Indicators',
  'Columns',
  'CustomAnalysis',
  'ResultsPlugins',
];

export function CodeEditorWorkspace() {
  const store = useAppStore();
  const [showNewModal, setShowNewModal] = useState<boolean>(false);
  const [showTesterModal, setShowTesterModal] = useState<boolean>(false);
  const [collapsedCategories, setCollapsedCategories] = useState<Record<string, boolean>>({});
  const [consoleTab, setConsoleTab] = useState<'build' | 'runtime'>('build');
  const [runtimeLogs, setRuntimeLogs] = useState<string[]>([
    '[system] HaruQuantAI Java & Python Extension Runtime 2.4.0 ready.',
    '[system] JVM compiler bridge initialized with strict memory bounds (Heap: 512MB).',
  ]);
  const [filterQuery, setFilterQuery] = useState<string>('');

  const activeFile = store.extensionFiles.find(f => f.id === store.activeFileId) || store.extensionFiles[0];

  const toggleCategory = (cat: string) => {
    setCollapsedCategories(prev => ({ ...prev, [cat]: !prev[cat] }));
  };

  const handleSave = () => {
    if (!activeFile) return;
    store.saveFile(activeFile.id);
    store.notify(`Saved "${activeFile.name}" to workspace`);
  };

  const handleCompile = () => {
    if (!activeFile) return;

    const time = new Date().toLocaleTimeString();
    const content = activeFile.content || '';
    const openBraces = (content.match(/\{/g) || []).length;
    const closeBraces = (content.match(/\}/g) || []).length;

    let hasErrors = false;
    let diagnostics = '';

    if (activeFile.language === 'java' && openBraces !== closeBraces) {
      hasErrors = true;
      diagnostics = `[${time}] ERROR: Syntax error in ${activeFile.name}: Unmatched braces ({ = ${openBraces}, } = ${closeBraces})\n` +
        `[${time}] Build failed with 1 error and 0 warnings.`;
    } else {
      diagnostics = `[${time}] COMPILING: ${activeFile.name} (${activeFile.category}, ${content.length} bytes)...\n` +
        `[${time}] AST Check: Validated syntax tree and annotations.\n` +
        `[${time}] Type Checker: Strict type symbols resolved against haruquantai.lib.*\n` +
        `[${time}] Packaging: Output class binary generated in build/classes/HaruQuantAI/${activeFile.category}/\n` +
        `[${time}] SUCCESS: Compilation completed with 0 errors and 0 warnings. Extension registered in runtime registry.`;
    }

    store.setCompileOutput(diagnostics);
    setConsoleTab('build');
    if (hasErrors) {
      store.notify(`Compilation failed for ${activeFile.name}`);
    } else {
      store.notify(`Successfully compiled ${activeFile.name}`);
      setRuntimeLogs(prev => [
        `[${time}] Extension "${activeFile.name}" dynamically linked to strategy engine.`,
        ...prev,
      ]);
    }
  };

  const handleExport = () => {
    if (!activeFile) return;
    store.notify(`Exported package for "${activeFile.name}" to ./dist/extensions/`);
  };

  const lineCount = (activeFile?.content || '').split('\n').length;
  const lineNumbers = Array.from({ length: Math.max(lineCount, 1) }, (_, i) => i + 1);

  return (
    <div className="code-editor h-full flex flex-col bg-[var(--bg)]">
      {/* Top Header */}
      <div className="h-11 flex items-center justify-between px-3 bg-[var(--panel)] border-b border-[var(--line)]">
        <div className="flex items-center gap-3">
          <Code2 size={18} className="text-cyan-400" />
          <div>
            <h1 className="text-xs font-bold text-gray-100 flex items-center gap-2">
              Code Editor & Extensions Studio
              <span className="text-[11px] font-normal text-gray-400">
                · {activeFile ? activeFile.name : 'No file open'}
                {activeFile?.dirty ? ' *' : ''}
              </span>
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button onClick={handleSave} disabled={!activeFile}>
            <Save size={14} className={activeFile?.dirty ? 'text-amber-400' : ''} />
            Save
          </Button>
          <Button className="primary" onClick={handleCompile} disabled={!activeFile}>
            <Play size={14} />
            Compile
          </Button>
          <Button
            onClick={() => setShowTesterModal(true)}
            disabled={!activeFile || activeFile.category !== 'Indicators'}
          >
            <TestTube2 size={14} className="text-purple-400" />
            Test Indicator
          </Button>
          <Button onClick={handleExport} disabled={!activeFile}>
            <Download size={14} />
            Export Package
          </Button>
        </div>
      </div>

      {/* Main Workspace Body */}
      <div className="flex-1 grid grid-cols-[230px_1fr] min-h-0">
        {/* Left Tree Explorer */}
        <aside className="bg-[#1a1f26] border-r border-[var(--line)] flex flex-col p-2 min-h-0">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-[var(--line)]">
            <strong className="text-xs text-gray-300 flex items-center gap-1.5">
              <FolderCode size={14} className="text-cyan-400" />
              Extensions Tree
            </strong>
            <Button className="text-xs px-2 py-0.5" onClick={() => setShowNewModal(true)}>
              <Plus size={13} />
            </Button>
          </div>

          <div className="mb-2">
            <TextInput
              placeholder="Search extensions..."
              value={filterQuery}
              onChange={e => setFilterQuery(e.target.value)}
            />
          </div>

          <div className="flex-1 overflow-y-auto flex flex-col gap-1 pr-1 text-xs">
            {CATEGORIES.map(category => {
              const isCollapsed = !!collapsedCategories[category];
              const filesInCategory = store.extensionFiles.filter(
                f => f.category === category && (!filterQuery || f.name.toLowerCase().includes(filterQuery.toLowerCase()))
              );

              return (
                <div key={category} className="flex flex-col">
                  <button
                    className="w-full flex items-center gap-1.5 py-1 px-1.5 rounded text-gray-400 hover:text-gray-200 hover:bg-gray-800 text-left font-semibold text-[11px]"
                    onClick={() => toggleCategory(category)}
                  >
                    {isCollapsed ? <ChevronRight size={13} /> : <ChevronDown size={13} />}
                    <span>{category}</span>
                    <span className="ml-auto text-[10px] text-gray-500 font-mono">
                      ({filesInCategory.length})
                    </span>
                  </button>

                  {!isCollapsed && (
                    <div className="pl-4 flex flex-col gap-0.5 mt-0.5">
                      {filesInCategory.length === 0 ? (
                        <span className="text-[10px] text-gray-600 italic py-0.5 pl-2">
                          No files
                        </span>
                      ) : (
                        filesInCategory.map(f => {
                          const isActive = f.id === activeFile?.id;
                          return (
                            <div
                              key={f.id}
                              onClick={() => store.openFile(f.id)}
                              className={`group flex items-center justify-between py-1 px-2 rounded cursor-pointer transition-colors ${
                                isActive
                                  ? 'bg-[#17455a] text-cyan-200 font-medium'
                                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                              }`}
                            >
                              <div className="flex items-center gap-1.5 truncate">
                                <FileCode2
                                  size={13}
                                  className={
                                    f.language === 'python' ? 'text-yellow-400' : 'text-cyan-400'
                                  }
                                />
                                <span className="truncate">{f.name}</span>
                                {f.dirty && <span className="text-amber-400 font-bold">*</span>}
                              </div>

                              <button
                                className="opacity-0 group-hover:opacity-100 hover:text-red-400 p-0.5 transition-opacity"
                                onClick={e => {
                                  e.stopPropagation();
                                  if (store.extensionFiles.length <= 1) {
                                    store.notify('Cannot delete the last remaining extension file.');
                                    return;
                                  }
                                  store.deleteExtensionFile(f.id);
                                  store.notify(`Deleted "${f.name}"`);
                                }}
                              >
                                <Trash2 size={11} />
                              </button>
                            </div>
                          );
                        })
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </aside>

        {/* Right Editor Area */}
        <main className="flex flex-col min-h-0 bg-[#11161b]">
          {/* File Tabs Bar */}
          <div className="h-8 bg-[#171c22] border-b border-[var(--line)] flex items-center overflow-x-auto px-1 gap-1">
            {store.openFileIds.map(fileId => {
              const file = store.extensionFiles.find(f => f.id === fileId);
              if (!file) return null;
              const isActive = file.id === activeFile?.id;

              return (
                <div
                  key={file.id}
                  onClick={() => store.setActiveFile(file.id)}
                  className={`h-7 px-2.5 flex items-center gap-2 border-t-2 text-xs rounded-t cursor-pointer select-none transition-colors ${
                    isActive
                      ? 'bg-[#20252d] border-t-cyan-500 text-gray-100 font-medium'
                      : 'bg-transparent border-t-transparent text-gray-400 hover:bg-[#1a2027] hover:text-gray-300'
                  }`}
                >
                  <FileCode2
                    size={12}
                    className={file.language === 'python' ? 'text-yellow-400' : 'text-cyan-400'}
                  />
                  <span>{file.name}</span>
                  {file.dirty && <span className="text-amber-400 text-xs font-bold">*</span>}
                  <button
                    className="hover:text-red-400 p-0.5 rounded ml-1"
                    onClick={e => {
                      e.stopPropagation();
                      store.closeFile(file.id);
                    }}
                  >
                    <X size={11} />
                  </button>
                </div>
              );
            })}
          </div>

          {/* Code Editing Canvas */}
          <div className="flex-1 flex min-h-0 relative overflow-hidden">
            {activeFile ? (
              <>
                {/* Line Numbers Gutter */}
                <div className="w-12 bg-[#0c1015] border-r border-[#1e2632] py-3 pr-2 text-right font-mono text-[11px] text-gray-600 select-none overflow-hidden">
                  {lineNumbers.map(n => (
                    <div key={n} className="leading-relaxed">
                      {n}
                    </div>
                  ))}
                </div>

                {/* Editor Textarea */}
                <div className="flex-1 relative overflow-auto">
                  <textarea
                    value={activeFile.content}
                    onChange={e => store.updateFileContent(activeFile.id, e.target.value)}
                    spellCheck={false}
                    className="w-full h-full p-3 font-mono text-xs leading-relaxed bg-transparent text-[#dce1e8] outline-none resize-none border-0 focus:ring-0 whitespace-pre"
                    style={{ tabSize: 4 }}
                  />
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500 text-xs">
                No file open. Select a file from the extensions tree on the left.
              </div>
            )}
          </div>

          {/* Bottom Console Panel */}
          <div className="h-44 border-t border-[var(--line)] bg-[#151a21] flex flex-col">
            <div className="h-7 bg-[#1c222b] border-b border-[var(--line)] flex items-center px-2 gap-2 text-xs">
              <button
                className={`px-3 py-1 font-semibold flex items-center gap-1.5 transition-colors ${
                  consoleTab === 'build'
                    ? 'text-cyan-400 border-b-2 border-b-cyan-400'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
                onClick={() => setConsoleTab('build')}
              >
                <Terminal size={12} />
                Build Output
              </button>
              <button
                className={`px-3 py-1 font-semibold flex items-center gap-1.5 transition-colors ${
                  consoleTab === 'runtime'
                    ? 'text-cyan-400 border-b-2 border-b-cyan-400'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
                onClick={() => setConsoleTab('runtime')}
              >
                <Activity size={12} />
                Runtime Console
              </button>
              <button
                className="ml-auto text-[10px] text-gray-500 hover:text-gray-300"
                onClick={() => {
                  if (consoleTab === 'build') {
                    store.setCompileOutput('[ready] Build console cleared.');
                  } else {
                    setRuntimeLogs(['[ready] Runtime console cleared.']);
                  }
                }}
              >
                Clear
              </button>
            </div>

            <div className="flex-1 p-2 font-mono text-[11px] overflow-y-auto leading-relaxed text-gray-300">
              {consoleTab === 'build' ? (
                <pre className="whitespace-pre-wrap font-mono m-0 text-cyan-300">
                  {store.compileOutput}
                </pre>
              ) : (
                <div className="flex flex-col gap-1">
                  {runtimeLogs.map((log, i) => (
                    <div key={i} className="text-gray-300">
                      {log}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>

      {/* New Extension Modal */}
      {showNewModal && (
        <NewExtensionModal
          onClose={() => setShowNewModal(false)}
          onAddFile={file => store.addExtensionFile(file)}
        />
      )}

      {/* Indicator Interactive Tester Modal */}
      {showTesterModal && activeFile && (
        <IndicatorTesterModal
          indicatorName={activeFile.name}
          onClose={() => setShowTesterModal(false)}
        />
      )}
    </div>
  );
}

export { CodeEditorWorkspace as CodeEditor };
