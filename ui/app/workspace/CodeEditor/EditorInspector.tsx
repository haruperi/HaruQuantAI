import React from 'react';
import { BookOpen, Copy, FileText, Layers } from 'lucide-react';
import type { CodeEditorState } from './useCodeEditorWorkspace';

export function EditorInspector({ workspace }: { workspace: CodeEditorState }) {
  const { activeTab, outlineSymbols } = workspace;
  return (
    <>
      {/* RIGHT COLUMN: OUTLINE & DOCUMENT INSPECTOR (Matching Overview1.png) */}
      <aside className="w-[300px] border-l border-slate-800 bg-slate-950/60 flex flex-col overflow-hidden flex-shrink-0">
        {/* Top Panel: Outline */}
        <div className="flex-1 flex flex-col border-b border-slate-800 overflow-hidden">
          <div className="px-3 py-2 border-b border-slate-800/80 bg-slate-900/40 text-xs font-semibold text-slate-300 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-blue-400" />
              Outline
            </span>
            <span className="text-[10px] text-slate-500">Symbols</span>
          </div>

          <div className="flex-1 overflow-y-auto p-2 font-mono text-[11px] space-y-2">
            {outlineSymbols.classes.length === 0 ? (
              <div className="text-slate-500 text-center py-6 text-xs">No classes detected in active file.</div>
            ) : (
              outlineSymbols.classes.map((cls, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex items-center gap-1.5 text-amber-300 font-semibold">
                    <Layers className="w-3.5 h-3.5 text-amber-400" />
                    <span>{cls.name}</span>
                    {cls.inherits && <span className="text-slate-500 font-normal text-[10px]">({cls.inherits})</span>}
                  </div>

                  {/* Attributes */}
                  {cls.attrs.length > 0 && (
                    <div className="pl-4 space-y-0.5 text-slate-400">
                      <div className="text-[10px] text-slate-500 uppercase">Attributes</div>
                      {cls.attrs.map((attr, aIdx) => (
                        <div key={aIdx} className="text-slate-300">
                          · {attr}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Methods */}
                  {cls.methods.length > 0 && (
                    <div className="pl-4 space-y-0.5 text-slate-400 pt-1">
                      <div className="text-[10px] text-slate-500 uppercase">Methods</div>
                      {cls.methods.map((m, mIdx) => (
                        <div key={mIdx} className="text-purple-300">
                          ƒ {m}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}

            {/* Imports Tree */}
            {outlineSymbols.imports.length > 0 && (
              <div className="pt-2 border-t border-slate-800/80 space-y-0.5">
                <div className="text-[10px] text-slate-500 uppercase">Imports ({outlineSymbols.imports.length})</div>
                {outlineSymbols.imports.slice(0, 8).map((imp, i) => (
                  <div key={i} className="text-slate-400 truncate">
                    {imp}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Bottom Panel: Document Card */}
        <div className="h-56 p-3 flex flex-col justify-between bg-slate-900/30 overflow-y-auto">
          <div>
            <div className="flex items-center justify-between text-xs font-semibold text-slate-300 pb-2 border-b border-slate-800">
              <span className="flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-emerald-400" />
                Document
              </span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-600/20 text-blue-300">Python 3.14</span>
            </div>

            {outlineSymbols.classes.length > 0 ? (
              <div className="mt-2 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-slate-100">{outlineSymbols.classes[0].name}</span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">Class</span>
                </div>

                {outlineSymbols.classes[0].inherits && (
                  <div className="text-[11px] text-slate-400">
                    Inherits: <span className="text-blue-400 font-mono">{outlineSymbols.classes[0].inherits}</span>
                  </div>
                )}

                <div className="text-[11px] text-slate-400 leading-relaxed bg-slate-950/60 p-2 rounded border border-slate-800">
                  Custom quantitative trading component inheriting from HaruQuantAI foundation contracts.
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-500 py-3">Open a file to inspect symbol metadata.</div>
            )}
          </div>

          <div className="pt-2 border-t border-slate-800/80 text-[11px] font-mono text-slate-400 truncate flex items-center justify-between">
            <span className="truncate">{activeTab?.file_path || 'No file selected'}</span>
            {activeTab && (
              <button
                onClick={() => navigator.clipboard.writeText(activeTab.file_path)}
                title="Copy Path"
                className="p-1 hover:text-slate-200"
              >
                <Copy className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}
