/// <reference types="vite/client" />
import { describe, expect, it } from 'vitest';
import manifest from '../../../../app/plugins/databank/DatabankRename/source-map.json';
import registry from '../../../../app/plugins/databank/README.md?raw';
import { RenameStrategiesDialog } from '../../../../app/plugins/databank/DatabankRename/ui/module';
import { useDatabankRenamePopup } from '../../../../app/plugins/databank/DatabankRename/ui/DatabankRenamePopupCtrl';
import { validateSourceMapping } from './sourceMappingValidation';
const prefix = '../../../../app/plugins/databank/DatabankRename/';
const files = Object.keys(import.meta.glob('../../../../app/plugins/databank/DatabankRename/**/*', { eager: true, query: '?raw', import: 'default' })).map(path => path.slice(prefix.length));
const scope = { plugin: 'DatabankRename', html: 1, js: 2, css: 1, excluded: 3 };
describe('DatabankRename structural mapping', () => {
  it('accounts for all counterparts, binary exclusion and target exception', () => {
    expect(validateSourceMapping(manifest, files, registry, scope)).toEqual([]);
    expect(files).toHaveLength(5);
    expect(manifest.sources.filter(s => s.target !== null)).toHaveLength(4);
    for (const component of [RenameStrategiesDialog, useDatabankRenamePopup]) expect(component).toBeTypeOf('function');
  });
  it('rejects omitted, mis-cased and unclassified files', () => {
    for (const changed of [files.filter(f => f !== 'ui/databankRenamePopup.tsx'), files.map(f => f === 'ui/databankRenamePopup.tsx' ? 'ui/DatabankRenamePopup.tsx' : f), [...files, 'unknown.ts']]) expect(validateSourceMapping(manifest, changed, registry, scope)).not.toEqual([]);
  });
  it('rejects collisions, wrong extensions, invalid locators and provenance', () => {
    for (const target of ['ui/module.ts', 'ui/databankRenamePopup.ts', '../screen.tsx', '/screen.tsx']) {
      const changed = structuredClone(manifest);
      changed.sources.find(s => s.relative_path === 'ui/databankRenamePopup.html')!.target = target;
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
