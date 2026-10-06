/// <reference types="vite/client" />
import { describe, expect, it } from 'vitest';
import sourceMap from '../../../../../app/plugins/data_source/Darwinex/source-map.json';
import { validateSourceMapping } from './sourceMappingValidation';
import { darwinexProvider } from '../../../../../app/plugins/data_source/Darwinex/module';
import { AddPopup } from '../../../../../app/plugins/data_source/Darwinex/add/module';
import { ImportPopup } from '../../../../../app/plugins/data_source/Darwinex/import/module';
import { DownloadPopup } from '../../../../../app/plugins/data_source/Darwinex/download/module';
import { DarwinexConsent, DarwinexDisclaimerPopup, useDarwinexDisclaimer } from '../../../../../app/plugins/data_source/Darwinex/disclaimer/module';
import { SelectInstrumentsPopup } from '../../../../../app/plugins/data_source/Darwinex/add/selectInstrumentsPopup';
const prefix = '../../../../../app/plugins/data_source/Darwinex/';
const rawFiles = import.meta.glob('../../../../../app/plugins/data_source/Darwinex/**/*', {
  eager: true,
  query: '?raw',
  import: 'default',
}) as Record<string, string>;
const files = Object.keys(rawFiles).map((path) => path.slice(prefix.length));
const registry = rawFiles[`${prefix}README.md`];

describe('Darwinex structural mapping', () => {
  it('accounts for every source and target with unique exact relative counterparts', () => {
    expect(validateSourceMapping(JSON.parse(JSON.stringify(sourceMap)), files, registry)).toEqual(
      [],
    );
    expect(sourceMap.sources.filter((source) => source.target !== null)).toHaveLength(17);
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
    expect(darwinexProvider.commands.map((command) => command.id)).toEqual([
      'darwinex-add',
      'darwinex-import',
      'darwinex-download',
    ]);
    for (const component of [AddPopup, ImportPopup, DownloadPopup, SelectInstrumentsPopup, DarwinexConsent, DarwinexDisclaimerPopup, useDarwinexDisclaimer])
      expect(component).toBeTypeOf('function');
  });
});

it('keeps target consent controlled and excludes donor legal prose', () => {
  let value = false;
  const element = DarwinexConsent({ agreed: false, setAgreed: next => { value = next; } });
  expect(element.type).toBe('label');
  element.props.children[0].props.onChange({ target: { checked: true } });
  expect(value).toBe(true);
  expect(rawFiles[`${prefix}disclaimer/darwinexDisclaimerPopup.tsx`]).not.toContain('Darwinex Bank SA');
});
