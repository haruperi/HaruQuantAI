import React from 'react';
import { AlertCircle, RefreshCw, Search, Terminal } from 'lucide-react';
import type { CodeEditorState } from './useCodeEditorWorkspace';

export function EditorBottomPanel({ workspace }: { workspace: CodeEditorState }) {
  const {
    bottomTab,
    setBottomTab,
    diagnostics,
    outputLogs,
    searchResults,
    searchQuery,
    setSearchQuery,
    activeTab,
    handleOpenPath,
    handleCompile,
    handleSearchInFiles,
  } = workspace;
  return (
    <>
      {/* BOTTOM DOCK PANEL (Problems / Output / Test Results / Search) */}
      <div className="h-48 border-t border-slate-800 bg-slate-950 flex flex-col flex-shrink-0">
        {/* Bottom Tabs Header */}
        <div className="h-8 border-b border-slate-800 bg-slate-900/70 flex items-center justify-between px-3 text-xs">
          <div className="flex items-center gap-1">
            <button
              onClick={() => setBottomTab('problems')}
              className={`px-3 py-1 flex items-center gap-1.5 transition-colors border-b-2 font-medium ${
                bottomTab === 'problems'
                  ? 'border-blue-500 text-blue-400 bg-slate-900'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>Problems</span>
              {diagnostics.length > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-rose-500/20 text-rose-300 font-mono">
                  {diagnostics.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setBottomTab('output')}
              className={`px-3 py-1 flex items-center gap-1.5 transition-colors border-b-2 font-medium ${
                bottomTab === 'output'
                  ? 'border-blue-500 text-blue-400 bg-slate-900'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>Output</span>
            </button>

            <button
              onClick={() => setBottomTab('search')}
              className={`px-3 py-1 flex items-center gap-1.5 transition-colors border-b-2 font-medium ${
                bottomTab === 'search'
                  ? 'border-blue-500 text-blue-400 bg-slate-900'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>Search</span>
            </button>

            <button
              onClick={() => setBottomTab('terminal')}
              className={`px-3 py-1 flex items-center gap-1.5 transition-colors border-b-2 font-medium ${
                bottomTab === 'terminal'
                  ? 'border-blue-500 text-blue-400 bg-slate-900'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>Terminal</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCompile}
              className="px-2 py-0.5 rounded text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1"
            >
              <RefreshCw className="w-3 h-3" /> Re-check
            </button>
          </div>
        </div>

        {/* Bottom Content Body */}
        <div className="flex-1 overflow-y-auto p-2">
          {bottomTab === 'problems' && (
            <div className="space-y-1 font-mono text-xs">
              {diagnostics.length === 0 ? (
                <div className="text-slate-500 py-4 text-center text-xs">
                  No syntax or compiler diagnostics detected.
                </div>
              ) : (
                diagnostics.map((diag, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-1.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 hover:bg-rose-500/20 transition-colors"
                  >
                    <span className="flex items-center gap-2">
                      <AlertCircle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
                      <span>
                        Line {diag.line}:{diag.column} — {diag.message}
                      </span>
                    </span>
                    <span className="text-[11px] text-slate-400">{activeTab?.title}</span>
                  </div>
                ))
              )}
            </div>
          )}

          {bottomTab === 'output' && (
            <div className="font-mono text-[11px] text-slate-300 space-y-1">
              {outputLogs.map((log, i) => (
                <div key={i} className="leading-relaxed text-slate-400">
                  {log}
                </div>
              ))}
            </div>
          )}

          {bottomTab === 'search' && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 max-w-md">
                <input
                  type="text"
                  placeholder="Find in snippets..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearchInFiles()}
                  className="flex-1 px-2.5 py-1 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200"
                />
                <button
                  onClick={handleSearchInFiles}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded"
                >
                  Find
                </button>
              </div>
              <div className="font-mono text-xs divide-y divide-slate-800">
                {searchResults.map((m, i) => (
                  <div
                    key={i}
                    onClick={() => handleOpenPath(m.file)}
                    className="py-1 cursor-pointer hover:bg-slate-900 px-1 rounded flex justify-between"
                  >
                    <span className="text-slate-300">
                      {m.file}:{m.line} — {m.text}
                    </span>
                    <span className="text-blue-400 font-semibold">{m.match}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {bottomTab === 'terminal' && (
            <div className="font-mono text-xs text-slate-400 p-2">
              <div>Use the application terminal to execute commands.</div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
