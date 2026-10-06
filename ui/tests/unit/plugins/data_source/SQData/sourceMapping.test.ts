/// <reference types="vite/client" />
import { describe, expect, it } from 'vitest';
import sourceMap from '../../../../../app/plugins/data_source/SQData/Equity/source-map.json';
import { validateSourceMapping } from './sourceMappingValidation';
import { equityProvider, runEquityUpdate } from '../../../../../app/plugins/data_source/SQData/Equity/module';
import { futuresProvider, runFuturesUpdate, SQFuturesAddPopup } from '../../../../../app/plugins/data_source/SQData/Futures/module';
import futuresMap from '../../../../../app/plugins/data_source/SQData/Futures/source-map.json';
import parentMap from '../../../../../app/plugins/data_source/SQData/source-map.json';
import { useSQEquityDataAdd } from '../../../../../app/plugins/data_source/SQData/Equity/add/SQEquityDataAddCtrl';
import { SQEquityAddPopup } from '../../../../../app/plugins/data_source/SQData/Equity/add/module';
const prefix = '../../../../../app/plugins/data_source/SQData/Equity/';
const rawFiles = import.meta.glob('../../../../../app/plugins/data_source/SQData/Equity/**/*', {
  eager: true,
  query: '?raw',
  import: 'default',
}) as Record<string, string>;
const files = Object.keys(rawFiles).map((path) => path.slice(prefix.length));
const allFiles = import.meta.glob('../../../../../app/plugins/data_source/SQData/**/*', { eager: true, query: '?raw', import: 'default' }) as Record<string,string>;
const rootPrefix = '../../../../../app/plugins/data_source/SQData/';
const registry = allFiles[`${rootPrefix}README.md`];

describe('SQData structural mapping', () => {
  it('qualifies Futures and parent delegation without collisions', () => {
    const futuresFiles = Object.keys(allFiles).filter(p => p.startsWith(rootPrefix+'Futures/')).map(p => p.slice((rootPrefix+'Futures/').length));
    expect(validateSourceMapping(futuresMap, futuresFiles, registry)).toEqual([]);
    expect(Object.keys(allFiles)).toHaveLength(24);
    expect(parentMap.children).toEqual(['Equity/source-map.json', 'Futures/source-map.json']);
    expect(Object.keys(allFiles).filter(p => !p.slice(rootPrefix.length).includes('/')).map(p=>p.slice(rootPrefix.length)).sort()).toEqual(parentMap.target_only.map(e=>e.path).sort());
    const labels: string[] = []; runEquityUpdate(label=>labels.push(label)); runFuturesUpdate(label=>labels.push(label));
    expect(labels).toEqual(['Equity dataset update','Futures dataset update']);
    expect(futuresProvider.commands.map(c=>c.id)).toEqual(['sq-futures-find','sq-futures-update']);
  });
  it('accounts for every source and target with unique exact relative counterparts', () => {
    expect(validateSourceMapping(JSON.parse(JSON.stringify(sourceMap)), files, registry)).toEqual(
      [],
    );
    expect(sourceMap.sources.filter((source) => source.target !== null)).toHaveLength(9);
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
      'SQEquityDataService.ts',
      'add/addPopup.ts',
      'C:/machine/screen.tsx',
      '../screen.tsx',
    ]) {
      const changed = structuredClone(sourceMap);
      changed.sources.find(
        (source) => source.relative_path === 'add/addPopup.html',
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
    expect(equityProvider.commands.map((command) => command.id)).toEqual([
      'sq-equity-find', 'sq-equity-update',
    ]);
    for (const component of [SQEquityAddPopup, useSQEquityDataAdd, SQFuturesAddPopup])
      expect(component).toBeTypeOf('function');
  });
});
