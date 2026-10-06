/// <reference types="vite/client" />
import { describe, expect, it } from 'vitest';
import sourceMap from '../../../../../app/plugins/data_source/Dukascopy/source-map.json';
import { validateSourceMapping } from './sourceMappingValidation';
import { dukascopyProvider } from '../../../../../app/plugins/data_source/Dukascopy/module';
import { AddPopup } from '../../../../../app/plugins/data_source/Dukascopy/add/module';
import { ImportPopup } from '../../../../../app/plugins/data_source/Dukascopy/import/module';
import {
  DisclaimerPopup,
  DisclaimerCdnDisclaimerPopup,
} from '../../../../../app/plugins/data_source/Dukascopy/disclaimer/module';

const prefix = '../../../../../app/plugins/data_source/Dukascopy/';
const rawFiles = import.meta.glob('../../../../../app/plugins/data_source/Dukascopy/**/*', {
  eager: true,
  query: '?raw',
  import: 'default',
}) as Record<string, string>;
const files = Object.keys(rawFiles).map((path) => path.slice(prefix.length));
const registry = rawFiles[`${prefix}README.md`];

describe('Dukascopy structural mapping', () => {
  it('accounts for every source and target with unique exact relative counterparts', () => {
    expect(validateSourceMapping(JSON.parse(JSON.stringify(sourceMap)), files, registry)).toEqual(
      [],
    );
    expect(sourceMap.sources.filter((source) => source.target !== null)).toHaveLength(16);
    expect(
      sourceMap.sources.filter((source) =>
        source.relative_path.endsWith('/cdnDisclaimerPopup.html'),
      ),
    ).toHaveLength(2);
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
      'add/selectInstrumentsPopup.ts',
      'C:/machine/screen.tsx',
      '../screen.tsx',
    ]) {
      const changed = structuredClone(sourceMap);
      changed.sources.find(
        (source) => source.relative_path === 'add/selectInstrumentsPopup.html',
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
    expect(dukascopyProvider.commands.map((command) => command.id)).toEqual([
      'dukascopy-add',
      'dukascopy-download',
      'dukascopy-information',
    ]);
    for (const component of [AddPopup, ImportPopup, DisclaimerPopup, DisclaimerCdnDisclaimerPopup])
      expect(component).toBeTypeOf('function');
  });
});
