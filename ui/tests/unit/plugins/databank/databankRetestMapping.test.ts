/// <reference types="vite/client" />
import { describe, expect, it } from 'vitest';
import manifest from '../../../../app/plugins/databank/ResultsDatabankActions/retest/source-map.json';
import registry from '../../../../app/plugins/databank/README.md?raw';
import { RetestDialog } from '../../../../app/plugins/databank/ResultsDatabankActions/retest/module';
import { validateSourceMapping } from './sourceMappingValidation';
const prefix = '../../../../app/plugins/databank/ResultsDatabankActions/retest/';
const files = Object.keys(import.meta.glob('../../../../app/plugins/databank/ResultsDatabankActions/retest/**/*', { eager: true, query: '?raw', import: 'default' })).map(path => path.slice(prefix.length));
const scope = { plugin: 'ResultsDatabankActions/retest', html: 1, js: 2, css: 0, excluded: 0 };
describe('ResultsDatabankActions/retest structural mapping', () => {
  it('accounts for all counterparts, binary exclusion and target exception', () => {
    expect(validateSourceMapping(manifest, files, registry, scope)).toEqual([]);
    expect(files).toHaveLength(4);
    expect(manifest.sources.filter(s => s.target !== null)).toHaveLength(3);
    for (const component of [RetestDialog]) expect(component).toBeTypeOf('function');
  });
  it('rejects omitted, mis-cased and unclassified files', () => {
    for (const changed of [files.filter(f => f !== 'retestDialog.tsx'), files.map(f => f === 'retestDialog.tsx' ? 'ResultsDatabankActions/retestPopup.tsx' : f), [...files, 'unknown.ts']]) expect(validateSourceMapping(manifest, changed, registry, scope)).not.toEqual([]);
  });
  it('rejects collisions, wrong extensions, invalid locators and provenance', () => {
    for (const target of ['module.ts', 'retestDialog.ts', '../screen.tsx', '/screen.tsx']) {
      const changed = structuredClone(manifest);
      changed.sources.find(s => s.relative_path === 'retestDialog.html')!.target = target;
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
