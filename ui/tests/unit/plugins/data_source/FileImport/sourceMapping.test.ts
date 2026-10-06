/// <reference types="vite/client" />
import { describe, expect, it } from 'vitest';
import sourceMap from '../../../../../app/plugins/data_source/FileImport/source-map.json';
import { validateSourceMapping } from './sourceMappingValidation';
import { filesProvider } from '../../../../../app/plugins/data_source/FileImport/module';
import { AddPopup } from '../../../../../app/plugins/data_source/FileImport/add/module';
import { ImportPopup } from '../../../../../app/plugins/data_source/FileImport/import/module';
import { MassImportPopup } from '../../../../../app/plugins/data_source/FileImport/massImport/module';
import { NewFormatPopup } from '../../../../../app/plugins/data_source/FileImport/import/newFormatPopup';
import { useFilesAdd } from '../../../../../app/plugins/data_source/FileImport/add/DataSourceFilesAddCtrl';
import { useFilesImport } from '../../../../../app/plugins/data_source/FileImport/import/DataSourceFilesImportCtrl';
import { useFilesMassImport } from '../../../../../app/plugins/data_source/FileImport/massImport/DataSourceFilesMassImportCtrl';
const prefix = '../../../../../app/plugins/data_source/FileImport/';
const rawFiles = import.meta.glob('../../../../../app/plugins/data_source/FileImport/**/*', {
  eager: true,
  query: '?raw',
  import: 'default',
}) as Record<string, string>;
const files = Object.keys(rawFiles).map((path) => path.slice(prefix.length));
const registry = rawFiles[`${prefix}README.md`];

describe('FileImport structural mapping', () => {
  it('accounts for every source and target with unique exact relative counterparts', () => {
    expect(validateSourceMapping(JSON.parse(JSON.stringify(sourceMap)), files, registry)).toEqual(
      [],
    );
    expect(sourceMap.sources.filter((source) => source.target !== null)).toHaveLength(13);
  });
  it('rejects missing files, casing drift and unclassified target files', () => {
    expect(
      validateSourceMapping(
        sourceMap,
        files.filter((file) => file !== 'add/addPopup.tsx'),
        registry,
      ),
    ).toContain('Missing target: add/addPopup.tsx');
    expect(
      validateSourceMapping(
        sourceMap,
        files.map((file) => (file === 'add/addPopup.tsx' ? 'add/AddPopup.tsx' : file)),
        registry,
      ),
    ).not.toEqual([]);
    expect(validateSourceMapping(sourceMap, [...files, 'unknown.ts'], registry)).toContain(
      'Unclassified target file: unknown.ts',
    );
  });
  it('rejects collisions, wrong extensions and absolute paths', () => {
    for (const path of [
      'add/addPopup.tsx',
      'import/importPopup.ts',
      'C:/machine/screen.tsx',
      '../screen.tsx',
    ]) {
      const changed = structuredClone(sourceMap);
      changed.sources.find(
        (source) => source.relative_path === 'import/importPopup.html',
      )!.target = path;
      expect(validateSourceMapping(changed, files, registry)).not.toEqual([]);
    }
  });
  it('rejects unresolved ownership, provenance and source IDs', () => {
    expect(validateSourceMapping(sourceMap, files, '')).not.toEqual([]);
    const changed = structuredClone(sourceMap);
    changed.sources[0].catalog_id = 'missing';
    changed.sources[0].sha256 = 'invalid';
    expect(validateSourceMapping(changed, files, registry)).toContain(
      'Unresolved source catalog: missing',
    );
    expect(validateSourceMapping(changed, files, registry)).toContain('Invalid fingerprint');
  });
  it('retains consumed command identities and callable component boundaries', () => {
    expect(filesProvider.commands.map((command) => command.id)).toEqual([
      'file-add',
      'file-import',
      'file-mass-import',
    ]);
    for (const component of [AddPopup, ImportPopup, MassImportPopup, NewFormatPopup, useFilesAdd, useFilesImport, useFilesMassImport])
      expect(component).toBeTypeOf('function');
  });
});

it('keeps the new-format name controlled and bounded', () => {
  let name = '';
  const view = NewFormatPopup({ name: 'Draft', onNameChange: value => { name = value; } });
  const input = view.props.children[1].props.children;
  expect(input.props.value).toBe('Draft');
  expect(input.props.maxLength).toBe(80);
  input.props.onChange({ target: { value: 'Saved format' } });
  expect(name).toBe('Saved format');
});
it('retains unsupported appImport as explicit exclusions and adds no command', () => {
  expect(sourceMap.sources.filter(source => source.relative_path.startsWith('appImport/')).every(source => source.classification === 'excluded' && source.target === null)).toBe(true);
  expect(files.some(file => file.startsWith('appImport/'))).toBe(false);
  const changed = structuredClone(sourceMap);
  changed.sources.find(source => source.relative_path === 'appImport/appImportPopup.html')!.target = 'appImport/appImportPopup.tsx';
  expect(validateSourceMapping(changed, files, registry)).toContain('Changed scoped exclusions');
});
