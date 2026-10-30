import React, { lazy, Suspense } from 'react';
import { Copy, FileCode, Folder, FolderPlus, Play, Plus, RefreshCw, Search, Target, Trash2, X } from 'lucide-react';

import { CreateFromTemplateModal } from './CreateFromTemplateModal';
import { ImportExportModal } from './ImportExportModal';
import { IndicatorTesterModal } from './IndicatorTesterModal';

import { EditorToolbar } from './EditorToolbar';
import { EditorBottomPanel } from './EditorBottomPanel';
import { EditorInspector } from './EditorInspector';
import { RenderTreeItem } from './EditorTreeItem';
import { useCodeEditorWorkspace } from './useCodeEditorWorkspace';

const SourceCodeEditor = lazy(() =>
  import('./SourceCodeEditor').then((module) => ({ default: module.SourceCodeEditor })),
);

export function CodeEditorWorkspace() {
  const workspace = useCodeEditorWorkspace();
  const {
    tabs,
    activeFilePath,
    setActiveFilePath,
    cursorPos,
    setCursorPos,
    treeRoot,
    collapsedFolders,
    setCollapsedFolders,
    navSearchQuery,
    setNavSearchQuery,
    selectedNavPath,
    setOutputLogs,
    searchQuery,
    showTemplateModal,
    setShowTemplateModal,
    showTesterModal,
    setShowTesterModal,
    showImportExportModal,
    setShowImportExportModal,
    contextMenu,
    setContextMenu,
    refreshNavigator,
    activeTab,
    activeContent,
    handleOpenPath,
    handleCloseTab,
    handleContentChange,
    handleContextMenuAction,
    diagnostics,
  } = workspace;

  return (
    <div className="h-full flex flex-col bg-slate-950 text-slate-100 select-none overflow-hidden font-sans">
      <EditorToolbar workspace={workspace} />
      {/* 2. MAIN 3-COLUMN WORKSPACE BODY */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT COLUMN: NAVIGATOR (Matching Overview1.png & File Context Menu.png) */}
        <aside className="w-[280px] border-r border-slate-800 bg-slate-950/60 flex flex-col overflow-hidden flex-shrink-0">
          <div className="px-3 py-2.5 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/40">
            <span className="text-xs font-semibold text-slate-300 flex items-center gap-2">
              <Folder className="w-3.5 h-3.5 text-blue-400" />
              Navigator
            </span>
            <div className="flex items-center gap-1 text-slate-400">
              <button
                onClick={refreshNavigator}
                title="Refresh Tree"
                className="p-1 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors"
              >
                <RefreshCw className="w-3 h-3" />
              </button>
              <button
                onClick={() => handleContextMenuAction('new_file')}
                title="New File"
                className="p-1 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => handleContextMenuAction('new_dir')}
                title="New Folder"
                className="p-1 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors"
              >
                <FolderPlus className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Navigator search filter */}
          <div className="p-2 border-b border-slate-800/60">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2" />
              <input
                type="text"
                placeholder="Search snippets..."
                value={navSearchQuery}
                onChange={(e) => setNavSearchQuery(e.target.value)}
                className="w-full pl-8 pr-2.5 py-1 text-xs bg-slate-900/90 border border-slate-800 rounded-md text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {/* Tree View */}
          <div className="flex-1 overflow-y-auto p-1.5 font-mono text-[11px] leading-relaxed">
            {treeRoot && (
              <RenderTreeItem
                item={treeRoot}
                collapsed={collapsedFolders}
                selectedPath={selectedNavPath}
                searchQuery={navSearchQuery}
                onToggle={(path) => setCollapsedFolders((p) => ({ ...p, [path]: !p[path] }))}
                onSelectFile={handleOpenPath}
                onContextMenu={(e, it) => {
                  e.preventDefault();
                  setContextMenu({ x: e.clientX, y: e.clientY, item: it });
                }}
              />
            )}
          </div>
        </aside>

        {/* MIDDLE COLUMN: CODE EDITOR & DOCUMENT TABS (Matching Overview1.png) */}
        <main className="flex-1 min-w-0 flex flex-col overflow-hidden bg-slate-950">
          {/* Document Tabs Row */}
          <div className="h-9 border-b border-slate-800 bg-slate-900/80 flex items-center px-1 overflow-x-auto flex-shrink-0">
            {tabs.map((tab) => {
              const isActive = tab.file_path === activeFilePath;
              return (
                <div
                  key={tab.file_path}
                  onClick={() => setActiveFilePath(tab.file_path)}
                  className={`group h-8 px-3 flex items-center gap-2 border-r border-slate-800/80 cursor-pointer text-xs font-mono transition-colors relative ${
                    isActive
                      ? 'bg-slate-950 text-slate-100 font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`}
                >
                  {isActive && <div className="absolute top-0 left-0 right-0 h-0.5 bg-blue-500" />}
                  <FileCode className={`w-3.5 h-3.5 ${isActive ? 'text-blue-400' : 'text-slate-500'}`} />
                  <span className="truncate max-w-[140px]">{tab.title}</span>
                  {tab.is_dirty && <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" />}
                  <button
                    aria-label={`Close ${tab.title}`}
                    onClick={(e) => handleCloseTab(tab.file_path, e)}
                    className="p-0.5 rounded opacity-0 group-hover:opacity-100 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-opacity"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              );
            })}

            <button
              onClick={() => setShowTemplateModal(true)}
              className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded transition-colors ml-1"
              title="New Tab from Template"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex-1 min-h-0 min-w-0 flex overflow-hidden relative">
            <Suspense fallback={<div className="p-3 text-xs text-slate-400">Loading code editor...</div>}>
              <SourceCodeEditor
                filePath={activeFilePath}
                value={activeContent}
                openPaths={tabs.map((tab) => tab.file_path)}
                diagnostics={diagnostics}
                onChange={handleContentChange}
                onCursorChange={setCursorPos}
              />
            </Suspense>
          </div>

          <EditorBottomPanel workspace={workspace} />
        </main>

        <EditorInspector workspace={workspace} />
      </div>

      {/* 3. BOTTOM STATUS BAR (Matching Overview1.png) */}
      <footer className="h-6 border-t border-slate-800 bg-slate-900/90 px-3 flex items-center justify-between text-[11px] font-mono text-slate-400 flex-shrink-0 z-20">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-slate-300">Ready</span>
        </div>

        <div className="flex items-center gap-4 text-slate-400">
          <span>Python 3.14.7</span>
          <span>UTF-8</span>
          <span>Spaces: 4</span>
          <span>
            Ln {cursorPos.line}, Col {cursorPos.col}
          </span>
          <span className="text-blue-400 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" /> main
          </span>
        </div>
      </footer>

      {/* 4. CONTEXT MENU (Matching File Context Menu.png) */}
      {contextMenu && (
        <div
          style={{ top: contextMenu.y, left: contextMenu.x }}
          className="fixed z-50 w-52 rounded-lg border border-slate-800 bg-slate-900/95 backdrop-blur-md shadow-2xl py-1 text-xs text-slate-200 animate-in fade-in duration-100"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => handleContextMenuAction('open')}
            className="w-full px-3 py-1.5 text-left hover:bg-blue-600 hover:text-white flex items-center justify-between"
          >
            <span>Open</span>
            <span className="text-[10px] text-slate-400">Enter</span>
          </button>

          <div className="my-1 border-t border-slate-800" />

          <button
            onClick={() => handleContextMenuAction('new_file')}
            className="w-full px-3 py-1.5 text-left hover:bg-blue-600 hover:text-white flex items-center gap-2"
          >
            <FileCode className="w-3.5 h-3.5" /> New File
          </button>
          <button
            onClick={() => handleContextMenuAction('new_dir')}
            className="w-full px-3 py-1.5 text-left hover:bg-blue-600 hover:text-white flex items-center gap-2"
          >
            <Folder className="w-3.5 h-3.5" /> New Folder
          </button>

          <div className="my-1 border-t border-slate-800" />

          <button
            onClick={() => handleContextMenuAction('clone')}
            className="w-full px-3 py-1.5 text-left hover:bg-blue-600 hover:text-white flex items-center gap-2"
          >
            <Copy className="w-3.5 h-3.5" /> Clone
          </button>
          <button
            onClick={() =>
              handleContextMenuAction('rename').catch((error) => setOutputLogs((prev) => [String(error), ...prev]))
            }
            className="w-full px-3 py-1.5 text-left hover:bg-blue-600 hover:text-white flex items-center justify-between"
          >
            <span>Rename</span>
            <span className="text-[10px] text-slate-400">F2</span>
          </button>
          <button
            onClick={() =>
              handleContextMenuAction('delete').catch((error) => setOutputLogs((prev) => [String(error), ...prev]))
            }
            className="w-full px-3 py-1.5 text-left hover:bg-rose-600 hover:text-white text-rose-400 flex items-center justify-between"
          >
            <span className="flex items-center gap-2">
              <Trash2 className="w-3.5 h-3.5" /> Delete
            </span>
            <span className="text-[10px] text-slate-400">Del</span>
          </button>

          <div className="my-1 border-t border-slate-800" />

          <button
            onClick={() => handleContextMenuAction('compile')}
            className="w-full px-3 py-1.5 text-left hover:bg-blue-600 hover:text-white flex items-center gap-2"
          >
            <Play className="w-3.5 h-3.5 text-emerald-400" /> Compile
          </button>
          <button
            onClick={() => handleContextMenuAction('test')}
            className="w-full px-3 py-1.5 text-left hover:bg-blue-600 hover:text-white flex items-center gap-2"
          >
            <Target className="w-3.5 h-3.5 text-purple-400" /> Test Indicator
          </button>

          <div className="my-1 border-t border-slate-800" />

          <button
            onClick={() => handleContextMenuAction('copy_path')}
            className="w-full px-3 py-1.5 text-left hover:bg-blue-600 hover:text-white flex items-center gap-2"
          >
            <Copy className="w-3.5 h-3.5" /> Copy Path
          </button>
        </div>
      )}

      {/* 5. MODALS */}
      {showTemplateModal && (
        <CreateFromTemplateModal
          onClose={() => setShowTemplateModal(false)}
          onSnippetCreated={(tabInfo) => {
            refreshNavigator();
            handleOpenPath(tabInfo.file_path);
          }}
        />
      )}

      {showTesterModal && (
        <IndicatorTesterModal
          onClose={() => setShowTesterModal(false)}
          indicatorName={activeTab?.title.replace(/\.py$/, '') || 'MovingAverage'}
        />
      )}

      {showImportExportModal && (
        <ImportExportModal
          onClose={() => setShowImportExportModal(false)}
          openFiles={tabs.map((t) => t.file_path)}
          onImportComplete={() => refreshNavigator()}
        />
      )}
    </div>
  );
}
