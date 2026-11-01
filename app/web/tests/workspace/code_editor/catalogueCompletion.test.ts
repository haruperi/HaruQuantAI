import { describe, expect, it } from 'vitest';
import { EditorState } from '@codemirror/state';
import { CompletionContext } from '@codemirror/autocomplete';
import { python } from '@codemirror/lang-python';
import { catalogueCompletion } from '../../../workspaces/code_editor/pythonEditorSupport';

const symbols = [{ name: 'Marker', module: 'app.extend.user.marker', file_path: 'app/extend/user/marker.py', kind: 'class' as const, members: ['member'] }];
const complete = (doc: string) => catalogueCompletion(new CompletionContext(EditorState.create({ doc, extensions: [python()] }), doc.length, true), symbols);

describe('typed catalogue completion', () => {
  it('offers public symbols and class members', () => {
    expect(complete('Mar')?.options.map(option => option.label)).toEqual(['Marker']);
    expect(complete('Marker.mem')?.options.map(option => option.label)).toEqual(['member']);
  });
  it('resolves a constructor binding and imported alias', () => {
    expect(complete('instance = Marker()\ninstance.mem')?.options.map(option => option.label)).toEqual(['member']);
    expect(complete('from app.extend.user.marker import Marker as Alias\nAlias.mem')?.options.map(option => option.label)).toEqual(['member']);
  });
  it('does not suggest catalogue symbols inside comments or strings', () => {
    expect(complete('# Mar')).toBeNull();
    expect(complete('"Mar')).toBeNull();
  });
});
