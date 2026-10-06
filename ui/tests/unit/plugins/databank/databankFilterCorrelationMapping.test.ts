/// <reference types="vite/client" />
import { describe, expect, it } from 'vitest';
import manifest from '../../../../app/plugins/databank/DatabankFilterByCorrelation/source-map.json';
import registry from '../../../../app/plugins/databank/README.md?raw';
import { FilterByCorrelationModal } from '../../../../app/plugins/databank/DatabankFilterByCorrelation/module';
import { validateSourceMapping } from './sourceMappingValidation';
const prefix = '../../../../app/plugins/databank/DatabankFilterByCorrelation/';
const files = Object.keys(import.meta.glob('../../../../app/plugins/databank/DatabankFilterByCorrelation/**/*', { eager: true, query: '?raw', import: 'default' })).map(path => path.slice(prefix.length));
const scope = { plugin: 'DatabankFilterByCorrelation', html: 1, js: 1, css: 0, excluded: 1 };
describe('DatabankFilterByCorrelation structural mapping', () => {
  it('accounts for all counterparts, binary exclusion and target exception', () => {
    expect(validateSourceMapping(manifest, files, registry, scope)).toEqual([]);
    expect(files).toHaveLength(3);
    expect(manifest.sources.filter(s => s.target !== null)).toHaveLength(2);
    for (const component of [FilterByCorrelationModal]) expect(component).toBeTypeOf('function');
  });
  it('rejects omitted, mis-cased and unclassified files', () => {
    for (const changed of [files.filter(f => f !== 'databankFilterByCorrelationPopup.tsx'), files.map(f => f === 'databankFilterByCorrelationPopup.tsx' ? 'DatabankFilterByCorrelationPopup.tsx' : f), [...files, 'unknown.ts']]) expect(validateSourceMapping(manifest, changed, registry, scope)).not.toEqual([]);
  });
  it('rejects collisions, wrong extensions, invalid locators and provenance', () => {
    for (const target of ['module.ts', 'databankFilterByCorrelationPopup.ts', '../screen.tsx', '/screen.tsx']) {
      const changed = structuredClone(manifest);
      changed.sources.find(s => s.relative_path === 'databankFilterByCorrelationPopup.html')!.target = target;
      expect(validateSourceMapping(changed, files, registry, scope)).not.toEqual([]);
    }
    const changed = structuredClone(manifest);
    changed.sources[0].catalog_id = 'missing';
    changed.sources[0].sha256 = 'invalid';
    changed.sources[0].artifact_locator = 'invalid';
    expect(validateSourceMapping(changed, files, registry, scope)).not.toEqual([]);
    expect(validateSourceMapping(manifest, files, '', scope)).not.toEqual([]);
  });
  it('rejects unaccounted binaries and incorrect exclusions', () => {
    const changed = structuredClone(manifest);
    changed.sources.find(s => s.target === null)!.classification = 'counterpart';
    expect(validateSourceMapping(changed, files, registry, scope)).not.toEqual([]);
  });
});
