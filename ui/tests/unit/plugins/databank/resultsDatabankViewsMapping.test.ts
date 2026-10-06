/// <reference types="vite/client" />
import { describe, expect, it } from 'vitest';
import manifest from '../../../../app/plugins/databank/ResultsDatabankViews/source-map.json';
import registry from '../../../../app/plugins/databank/README.md?raw';
import { ManageViewsDialog } from '../../../../app/plugins/databank/ResultsDatabankViews/module';
import { useDatabankViewsDialog } from '../../../../app/plugins/databank/ResultsDatabankViews/DatabankViewsCtrl';
import { useDatabankViewsService } from '../../../../app/plugins/databank/ResultsDatabankViews/DatabankViewsService';
import { validateSourceMapping } from './sourceMappingValidation';
const prefix = '../../../../app/plugins/databank/ResultsDatabankViews/';
const files = Object.keys(import.meta.glob('../../../../app/plugins/databank/ResultsDatabankViews/**/*', { eager: true, query: '?raw', import: 'default' })).map(path => path.slice(prefix.length));
const scope = { plugin: 'ResultsDatabankViews', html: 1, js: 3, css: 1, excluded: 1 };
describe('ResultsDatabankViews structural mapping', () => {
  it('accounts for all counterparts, binary exclusion and target exception', () => {
    expect(validateSourceMapping(manifest, files, registry, scope)).toEqual([]);
    expect(files).toHaveLength(6);
    expect(manifest.sources.filter(s => s.target !== null)).toHaveLength(5);
    for (const component of [ManageViewsDialog, useDatabankViewsDialog, useDatabankViewsService]) expect(component).toBeTypeOf('function');
  });
  it('rejects omitted, mis-cased and unclassified files', () => {
    for (const changed of [files.filter(f => f !== 'databankViews.tsx'), files.map(f => f === 'databankViews.tsx' ? 'DatabankViews.tsx' : f), [...files, 'unknown.ts']]) expect(validateSourceMapping(manifest, changed, registry, scope)).not.toEqual([]);
  });
  it('rejects collisions, wrong extensions, invalid locators and provenance', () => {
    for (const target of ['module.ts', 'databankViews.ts', '../screen.tsx', '/screen.tsx']) {
      const changed = structuredClone(manifest);
      changed.sources.find(s => s.relative_path === 'databankViews.html')!.target = target;
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
