import React from 'react';
import {
  ChevronDown,
  Download,
  Folder,
  MoreHorizontal,
  Play,
  Plus,
  Save,
  Sparkles,
  Target,
  Upload,
} from 'lucide-react';
import type { CodeEditorState } from './useCodeEditorWorkspace';

export function EditorToolbar({ workspace }: { workspace: CodeEditorState }) {
  const {
    activeFilePath,
    setShowTemplateModal,
    setShowTesterModal,
    setShowImportExportModal,
    refreshNavigator,
    activeTab,
    handleSave,
    handleSaveAs,
    isDocumentCommandRunning,
    handleSaveAll,
    handleCompile,
  } = workspace;
  return (
    <>
      {/* 1. TOP TOOLBAR (Matching Top-menu.png) */}
      <div className="h-11 border-b border-slate-800 bg-slate-900/90 px-3 flex items-center justify-between flex-shrink-0 z-20">
        <div className="flex items-center gap-1.5">
          {/* New dropdown */}
          <div className="relative group">
            <button
              onClick={() => setShowTemplateModal(true)}
              className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New</span>
              <ChevronDown className="w-3 h-3 text-blue-200" />
            </button>
          </div>

          {/* Open */}
          <button
            onClick={refreshNavigator}
            className="px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-slate-100 text-xs font-medium flex items-center gap-1.5 transition-colors border border-slate-700/60"
          >
            <Folder className="w-3.5 h-3.5 text-slate-400" />
            <span>Open</span>
            <ChevronDown className="w-3 h-3 text-slate-500" />
          </button>

          {/* Save */}
          <button
            onClick={handleSave}
            disabled={!activeTab?.is_dirty || workspace.activeProtected || isDocumentCommandRunning}
            className="px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-slate-100 text-xs font-medium flex items-center gap-1.5 transition-colors border border-slate-700/60 disabled:opacity-40"
          >
            <Save className={`w-3.5 h-3.5 ${activeTab?.is_dirty ? 'text-amber-400' : 'text-slate-400'}`} />
            <span>Save</span>
          </button>

          {/* Save All */}
          <button
            onClick={handleSaveAs}
            disabled={!activeFilePath || isDocumentCommandRunning}
            className="px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-slate-300 text-xs border border-slate-700/60 disabled:opacity-40"
          >
            {isDocumentCommandRunning ? 'Saving As...' : 'Save As'}
          </button>

          <button
            onClick={handleSaveAll}
            className="px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-slate-100 text-xs font-medium flex items-center gap-1.5 transition-colors border border-slate-700/60"
          >
            <Save className="w-3.5 h-3.5 text-slate-400" />
            <span>Save All</span>
          </button>

          {/* Create from Template */}
          <button
            onClick={() => setShowTemplateModal(true)}
            className="px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-200 text-xs font-medium flex items-center gap-1.5 transition-colors border border-slate-700/70"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Create from Template</span>
            <ChevronDown className="w-3 h-3 text-slate-500" />
          </button>

          {/* Compile */}
          <button
            onClick={handleCompile}
            disabled={!activeFilePath || isDocumentCommandRunning || Boolean(workspace.compilation && !['COMPLETED', 'FAILED', 'CANCELLED', 'INTERRUPTED'].includes(workspace.compilation.status))}
            className="px-3 py-1.5 rounded-lg bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 text-xs font-medium flex items-center gap-1.5 transition-colors disabled:opacity-40"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Compile</span>
          </button>

          {/* Test Indicator */}
          <button
            onClick={() => setShowTesterModal(true)}
            className="px-3 py-1.5 rounded-lg bg-purple-600/10 hover:bg-purple-600/20 text-purple-400 border border-purple-500/30 text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <Target className="w-3.5 h-3.5" />
            <span>Test Indicator</span>
          </button>
        </div>

        {/* Right action group */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowImportExportModal(true)}
            className="px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-slate-100 text-xs font-medium flex items-center gap-1.5 transition-colors border border-slate-700/60"
          >
            <Upload className="w-3.5 h-3.5 text-blue-400" />
            <span>Import</span>
            <ChevronDown className="w-3 h-3 text-slate-500" />
          </button>

          <button
            onClick={() => setShowImportExportModal(true)}
            className="px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-slate-100 text-xs font-medium flex items-center gap-1.5 transition-colors border border-slate-700/60"
          >
            <Download className="w-3.5 h-3.5 text-emerald-400" />
            <span>Export</span>
            <ChevronDown className="w-3 h-3 text-slate-500" />
          </button>

          <button className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors">
            <MoreHorizontal className="w-4 h-4" />
          </button>
        </div>
      </div>
    </>
  );
}
