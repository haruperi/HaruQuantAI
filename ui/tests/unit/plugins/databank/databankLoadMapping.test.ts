/// <reference types="vite/client" />
import { describe, expect, it } from 'vitest';
import manifest from '../../../../app/plugins/databank/ResultsDatabankActions/load/source-map.json';
import registry from '../../../../app/plugins/databank/README.md?raw';
import { LoadRecordsDialog } from '../../../../app/plugins/databank/ResultsDatabankActions/load/module';
import { validateSourceMapping } from './sourceMappingValidation';
const prefix = '../../../../app/plugins/databank/ResultsDatabankActions/load/';
const files = Object.keys(import.meta.glob('../../../../app/plugins/databank/ResultsDatabankActions/load/**/*', { eager: true, query: '?raw', import: 'default' })).map(path => path.slice(prefix.length));
const scope = { plugin: 'ResultsDatabankActions/load', html: 1, js: 4, css: 1, excluded: 0 };
describe('ResultsDatabankActions/load structural mapping', () => {
  it('accounts for all counterparts, binary exclusion and target exception', () => {
    expect(validateSourceMapping(manifest, files, registry, scope)).toEqual([]);
    expect(files).toHaveLength(7);
    expect(manifest.sources.filter(s => s.target !== null)).toHaveLength(6);
    for (const component of [LoadRecordsDialog]) expect(component).toBeTypeOf('function');
  });
  it('rejects omitted, mis-cased and unclassified files', () => {
    for (const changed of [files.filter(f => f !== 'loadPopup.tsx'), files.map(f => f === 'loadPopup.tsx' ? 'ResultsDatabankActions/loadPopup.tsx' : f), [...files, 'unknown.ts']]) expect(validateSourceMapping(manifest, changed, registry, scope)).not.toEqual([]);
  });
  it('rejects collisions, wrong extensions, invalid locators and provenance', () => {
    for (const target of ['module.ts', 'loadPopup.ts', '../screen.tsx', '/screen.tsx']) {
      const changed = structuredClone(manifest);
      changed.sources.find(s => s.relative_path === 'loadPopup.html')!.target = target;
      expect(validateSourceMapping(changed, files, registry, scope)).not.toEqual([]);
    }
    const changed = structuredClone(manifest);
    changed.sources[0].catalog_id = 'missing';
    changed.sources[0].sha256 = 'invalid';
    changed.sources[0].artifact_locator = 'invalid';
    expect(validateSourceMapping(changed, files, registry, scope)).not.toEqual([]);
    expect(validateSourceMapping(manifest, files, '', scope)).not.toEqual([]);
  });
});
