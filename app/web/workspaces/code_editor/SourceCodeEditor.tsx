import { useLayoutEffect, useRef } from 'react';
import { basicSetup } from 'codemirror';
import { acceptCompletion, autocompletion } from '@codemirror/autocomplete';
import { indentWithTab } from '@codemirror/commands';
import { python } from '@codemirror/lang-python';
import { indentUnit, syntaxHighlighting } from '@codemirror/language';
import { setDiagnostics, type Diagnostic } from '@codemirror/lint';
import { Compartment, EditorState, Transaction, type Extension } from '@codemirror/state';
import { EditorView, keymap, placeholder } from '@codemirror/view';
import type { SyntaxDiagnosticDto } from './codeEditorClient';
import { codeEditorTheme, pythonBuiltinHighlight, pythonHighlightStyle } from './pythonEditorSupport';

interface SourceCodeEditorProps {
  filePath: string | null;
  value: string;
  openPaths: string[];
  diagnostics: SyntaxDiagnosticDto[];
  onChange: (value: string) => void;
  onCursorChange: (position: { line: number; col: number }) => void;
}

export function SourceCodeEditor(props: SourceCodeEditorProps) {
  const container = useRef<HTMLDivElement>(null);
  const view = useRef<EditorView | null>(null);
  const current = useRef(props);
  const currentPath = useRef<string | null>(null);
  const documents = useRef(new Map<string, { state: EditorState; scrollTop: number; scrollLeft: number }>());
  const syncing = useRef(false);
  const extensions = useRef<Extension[]>([]);
  const language = useRef(new Compartment());
  const editable = useRef(new Compartment());
  current.current = props;

  useLayoutEffect(() => {
    if (!container.current) return;
    extensions.current = [
      basicSetup,
      autocompletion({ interactionDelay: 0 }),
      keymap.of([{ key: 'Tab', run: acceptCompletion }, indentWithTab]),
      indentUnit.of('    '),
      language.current.of([]),
      editable.current.of(EditorView.editable.of(false)),
      codeEditorTheme,
      syntaxHighlighting(pythonHighlightStyle),
      placeholder('Choose a file from Navigator or create a new component.'),
      EditorView.contentAttributes.of({
        'aria-label': 'Source code editor',
        role: 'textbox',
        'aria-multiline': 'true',
        spellcheck: 'false',
      }),
      EditorView.updateListener.of((update) => {
        if (update.docChanged && !syncing.current) current.current.onChange(update.state.doc.toString());
        if (update.selectionSet || update.docChanged) {
          const head = update.state.selection.main.head;
          const line = update.state.doc.lineAt(head);
          current.current.onCursorChange({ line: line.number, col: head - line.from + 1 });
        }
      }),
    ];
    const editor = new EditorView({ parent: container.current, extensions: extensions.current });
    view.current = editor;
    return () => {
      editor.destroy();
      view.current = null;
      documents.current.clear();
      currentPath.current = null;
    };
  }, []);

  useLayoutEffect(() => {
    const editor = view.current;
    if (!editor) return;
    syncing.current = true;
    try {
      if (currentPath.current !== props.filePath) {
        if (currentPath.current)
          documents.current.set(currentPath.current, {
            state: editor.state,
            scrollTop: editor.scrollDOM.scrollTop,
            scrollLeft: editor.scrollDOM.scrollLeft,
          });
        const saved = props.filePath ? documents.current.get(props.filePath) : undefined;
        editor.setState(saved?.state ?? EditorState.create({ doc: props.value, extensions: extensions.current }));
        editor.dispatch({
          effects: [
            language.current.reconfigure(props.filePath?.endsWith('.py') ? [python(), pythonBuiltinHighlight] : []),
            editable.current.reconfigure(EditorView.editable.of(Boolean(props.filePath))),
          ],
        });
        currentPath.current = props.filePath;
        editor.scrollDOM.scrollTop = saved?.scrollTop ?? 0;
        editor.scrollDOM.scrollLeft = saved?.scrollLeft ?? 0;
      }
      if (editor.state.doc.toString() !== props.value)
        editor.dispatch({
          changes: { from: 0, to: editor.state.doc.length, insert: props.value },
          annotations: Transaction.addToHistory.of(false),
        });
      const head = editor.state.selection.main.head;
      const line = editor.state.doc.lineAt(head);
      current.current.onCursorChange({ line: line.number, col: head - line.from + 1 });
    } finally {
      syncing.current = false;
    }
  }, [props.filePath, props.value]);

  useLayoutEffect(() => {
    const open = new Set(props.openPaths);
    for (const path of documents.current.keys()) if (!open.has(path)) documents.current.delete(path);
  }, [props.openPaths]);

  useLayoutEffect(() => {
    const editor = view.current;
    if (!editor) return;
    const diagnostics: Diagnostic[] = props.diagnostics.map((item) => {
      const line = editor.state.doc.line(Math.max(1, Math.min(item.line, editor.state.doc.lines)));
      const from = Math.min(line.to, line.from + Math.max(0, item.column - 1));
      return { from, to: Math.min(line.to, from + 1), severity: item.severity, message: item.message };
    });
    editor.dispatch(setDiagnostics(editor.state, diagnostics));
  }, [props.diagnostics, props.filePath]);

  return <div ref={container} className="h-full min-h-0 min-w-0 flex-1 overflow-hidden" />;
}
