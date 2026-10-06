import { describe, expect, it } from 'vitest';
import { validateSourceMapping, type SourceMapping, type MappingScope } from '../databank/sourceMappingValidation';
import registry from '../../../../app/plugins/project/README.md?raw';
const root = '../../../../app/plugins/project/';
const rawFiles = import.meta.glob('../../../../app/plugins/project/**/*', { eager: true, query: '?raw', import: 'default' }) as Record<string, string>;
const scopes: MappingScope[] = [{"css":1,"allowFrontendExclusions":true,"plugin":"EnginePanel","excluded":14,"html":3,"js":2,"domain":"project"},{"css":0,"allowFrontendExclusions":true,"plugin":"ProjectSettings","excluded":3,"html":1,"js":1,"domain":"project"},{"css":0,"allowFrontendExclusions":true,"plugin":"SettingsPanel","excluded":1,"html":1,"js":2,"domain":"project"},{"css":1,"allowFrontendExclusions":true,"plugin":"ProjectResults","excluded":0,"html":2,"js":2,"domain":"project"},{"css":1,"allowFrontendExclusions":true,"plugin":"ResultsEquityChart","excluded":2,"html":2,"js":4,"domain":"project"},{"css":1,"allowFrontendExclusions":true,"plugin":"ResultsOverview","excluded":8,"html":1,"js":2,"domain":"project"},{"css":1,"allowFrontendExclusions":true,"plugin":"ResultsTradeList","excluded":1,"html":1,"js":2,"domain":"project"},{"css":0,"allowFrontendExclusions":true,"plugin":"ResultsTradelistViews","excluded":3,"html":1,"js":2,"domain":"project"}];
describe('project bounded structural inventories', () => {
  for (const scope of scopes) it(scope.plugin, () => {
    const prefix = root + scope.plugin + '/';
    const mapping = JSON.parse(rawFiles[prefix + 'source-map.json']) as SourceMapping;
    const childRoots = Object.keys(rawFiles).filter(path => path.startsWith(prefix) && path.endsWith('/source-map.json') && path !== prefix + 'source-map.json').map(path => path.slice(0, -'source-map.json'.length));
    const files = Object.keys(rawFiles).filter(path => path.startsWith(prefix) && !childRoots.some(child => path.startsWith(child))).map(path => path.slice(prefix.length));
    expect(validateSourceMapping(mapping, files, registry, scope)).toEqual([]);
    const drift = structuredClone(mapping);
    drift.sources[0].sha256 = 'invalid';
    expect(validateSourceMapping(drift, files, registry, scope)).toContain('Invalid fingerprint');
    expect(validateSourceMapping(mapping, [...files, 'unclassified.ts'], registry, scope)).toContain('Unclassified target file: unclassified.ts');
  });
});
