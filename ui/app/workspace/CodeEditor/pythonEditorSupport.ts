import { HighlightStyle, syntaxTree } from '@codemirror/language';
import { Decoration, EditorView, MatchDecorator, ViewPlugin, type ViewUpdate } from '@codemirror/view';
import { tags } from '@lezer/highlight';

export const pythonHighlightStyle = HighlightStyle.define([
  { tag: tags.keyword, color: '#c792ea' },
  { tag: [tags.variableName, tags.propertyName], color: '#9cdcfe' },
  { tag: [tags.className, tags.typeName], color: '#4ec9b0' },
  { tag: tags.definition(tags.className), color: '#4ec9b0', fontWeight: '600' },
  { tag: [tags.function(tags.variableName), tags.function(tags.propertyName)], color: '#dcdcaa' },
  { tag: [tags.string, tags.special(tags.string)], color: '#ce9178' },
  { tag: tags.comment, color: '#6a9955', fontStyle: 'italic' },
  { tag: tags.number, color: '#b5cea8' },
  { tag: [tags.bool, tags.null], color: '#569cd6' },
  { tag: tags.operator, color: '#d4d4d4' },
  { tag: [tags.meta, tags.annotation], color: '#d7ba7d' },
  { tag: tags.punctuation, color: '#cbd5e1' },
]);

const builtins = new Set(
  (
    'abs all any ascii bin bool breakpoint bytearray bytes callable chr classmethod compile complex delattr dict dir ' +
    'divmod enumerate eval exec filter float format frozenset getattr globals hasattr hash help hex id input int ' +
    'isinstance issubclass iter len list locals map max memoryview min next object oct open ord pow print property ' +
    'range repr reversed round set setattr slice sorted staticmethod str sum super tuple type vars zip __import__'
  ).split(' '),
);

const builtinMatcher = new MatchDecorator({
  regexp: /\b[A-Za-z_][A-Za-z_0-9]*\b/g,
  decorate(add, from, to, match, view) {
    const name = match[0];
    if (
      (!builtins.has(name) && name !== 'self' && name !== 'cls') ||
      syntaxTree(view.state).resolveInner(from, 1).name !== 'VariableName'
    )
      return;
    add(from, to, Decoration.mark({ class: builtins.has(name) ? 'cm-python-builtin' : 'cm-python-self' }));
  },
});

export const pythonBuiltinHighlight = ViewPlugin.fromClass(
  class {
    decorations;
    constructor(view: EditorView) {
      this.decorations = builtinMatcher.createDeco(view);
    }
    update(update: ViewUpdate) {
      this.decorations =
        syntaxTree(update.startState) !== syntaxTree(update.state)
          ? builtinMatcher.createDeco(update.view)
          : builtinMatcher.updateDeco(update, this.decorations);
    }
  },
  { decorations: (plugin) => plugin.decorations },
);

export const codeEditorTheme = EditorView.theme(
  {
    '&': { height: '100%', backgroundColor: '#020617', color: '#e2e8f0', fontSize: '12px' },
    '&.cm-focused': { outline: 'none' },
    '.cm-scroller': { overflow: 'auto', fontFamily: 'Consolas, "Cascadia Code", monospace', lineHeight: '20px' },
    '.cm-content': { padding: '12px 0', caretColor: '#e2e8f0' },
    '.cm-line': { padding: '0 12px' },
    '.cm-gutters': { backgroundColor: '#020617', color: '#64748b', borderRight: '1px solid #1e293b' },
    '.cm-activeLine, .cm-activeLineGutter': { backgroundColor: '#0f172a' },
    '.cm-cursor, .cm-dropCursor': { borderLeftColor: '#e2e8f0' },
    '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection': { backgroundColor: '#1e40af66' },
    '.cm-python-builtin, .cm-python-builtin span': { color: '#4fc1ff' },
    '.cm-python-self, .cm-python-self span': { color: '#f78c6c' },
    '.cm-matchingBracket': { backgroundColor: '#334155', outline: '1px solid #64748b' },
    '.cm-tooltip': { backgroundColor: '#0f172a', color: '#e2e8f0', border: '1px solid #334155' },
    '.cm-tooltip-autocomplete > ul > li[aria-selected]': { backgroundColor: '#1d4ed8', color: '#fff' },
    '.cm-search': { backgroundColor: '#0f172a' },
  },
  { dark: true },
);
