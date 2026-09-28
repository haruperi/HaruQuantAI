/* Resolve frontend edges using the installed compiler, including re-exports. */
const fs = require('fs');
const path = require('path');
const root = process.cwd();
const ts = require(path.join(root, 'app/ui/node_modules/typescript'));
const issues = [];
const owners = new Map();
const manifests = [];
const sourceRoots = ['app/ui/app/workspace', 'app/ui/app/plugins'];
const normalize = p => p.replaceAll('\\', '/');
const configPath = path.join(root, 'app/ui/tsconfig.app.json');
const configFile = ts.readConfigFile(configPath, ts.sys.readFile);
const parsedConfig = ts.parseJsonConfigFileContent(configFile.config ?? {}, ts.sys, path.dirname(configPath));
if (configFile.error || parsedConfig.errors.length) issues.push({path:normalize(path.relative(root,configPath)),code:'invalid_typescript_config'});
const compilerOptions = parsedConfig.options;
function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, {withFileTypes:true}).flatMap(item => {
    const p = path.join(dir,item.name);
    if (item.isSymbolicLink()) { issues.push({path:normalize(p),code:'linked_source'}); return []; }
    if (['node_modules','dist','__pycache__'].includes(item.name)) return [];
    return item.isDirectory() ? walk(p) : [normalize(p)];
  });
}
const files = walk(path.join(root,'app/ui/app')).concat(walk(path.join(root,'app/ui/tests')));
for (const prefix of ['app/workspace','app/plugins',...sourceRoots]) {
  for(const file of walk(path.join(root,prefix)).filter(p => p.endsWith('/package.json'))) {
    try {
      const doc = JSON.parse(fs.readFileSync(file,'utf8'));
      manifests.push(doc);
      for(const list of Object.values(doc.owned_paths || {})) for(const name of list) {
        if(owners.has(name)) issues.push({path:name,code:'overlapping_owner'});
        owners.set(name,doc.id);
      }
    } catch { issues.push({path:normalize(path.relative(root,file)),code:'invalid_manifest'}); }
  }
}
// Inspect declaration literals without executing contribution modules or loaders.
for (const doc of manifests) {
  if (!doc.ui_entry) continue;
  const file = path.resolve(root, doc.ui_entry);
  if (!fs.existsSync(file)) { issues.push({path:doc.ui_entry,code:'missing_ui_entry'}); continue; }
  const tree = ts.createSourceFile(file,fs.readFileSync(file,'utf8'),ts.ScriptTarget.Latest,true);
  const declarations = tree.statements.filter(ts.isVariableStatement).flatMap(n=>n.declarationList.declarations)
    .filter(n=>ts.isIdentifier(n.name)&&n.name.text==='contribution');
  const entry = declarations.length===1 ? declarations[0].initializer : undefined;
  if (!entry || !ts.isObjectLiteralExpression(entry)) { issues.push({path:doc.ui_entry,code:'nonliteral_ui_identity'}); continue; }
  const fields = new Map();
  for (const member of entry.properties) {
    if (!ts.isPropertyAssignment(member) || (!ts.isIdentifier(member.name)&&!ts.isStringLiteral(member.name))) {
      issues.push({path:doc.ui_entry,code:'computed_ui_metadata'}); continue;
    }
    if(fields.has(member.name.text)) issues.push({path:doc.ui_entry,code:'duplicate_ui_metadata'});
    fields.set(member.name.text,member.initializer);
  }
  const expected = {id:doc.id,kind:doc.kind,version:doc.version,owner:doc.owner_workspace_id??undefined,
    slot:doc.attachment?.slot_id,contractVersion:doc.attachment?.contract_version};
  for (const [key,value] of Object.entries(expected)) {
    const actual=fields.get(key);
    if (value===undefined ? actual!==undefined : !actual||!ts.isStringLiteral(actual)||actual.text!==value)
      issues.push({path:doc.ui_entry,code:'ui_manifest_identity_mismatch',field:key});
  }
}
function owner(file) {
  const name=normalize(path.relative(root,file));
  if(owners.has(name)) return owners.get(name);
  if(name.startsWith('app/ui/app/host/') || name.startsWith('app/ui/tests/unit/host/')) return 'host';
  if(name.startsWith('app/ui/app/components/')) return 'host.ui';
  if(name==='app/ui/tests/e2e/shellTestUtils.ts') return 'host.ui';
  return null;
}
function edge(file, specifier, node, tree) {
  let target = ts.resolveModuleName(specifier,file,compilerOptions,ts.sys).resolvedModule?.resolvedFileName;
  if(!target && specifier.startsWith('.')) {
    const literal=path.resolve(path.dirname(file),specifier.split('?')[0]);
    target=[literal,...['.ts','.tsx','.css','.json','/index.ts','/index.tsx'].map(s=>literal+s)].find(p=>fs.existsSync(p)&&fs.statSync(p).isFile());
  }
  if(target && !normalize(target).includes('/node_modules/')) {
    const from=owner(file), to=owner(target), name=normalize(path.relative(root,target));
    const allowed=(from!==null && from===to) || to==='host' || to==='host.ui';
    if(!allowed || !name.startsWith('app/ui/')) issues.push({path:normalize(path.relative(root,file)),target:name,code:'cross_owner_import',line:tree.getLineAndCharacterOfPosition(node.getStart()).line+1});
  } else if(specifier.startsWith('.') || specifier.startsWith('@/')) {
    issues.push({path:normalize(path.relative(root,file)),target:specifier,code:'unresolved_local_import'});
  }
}
for(const file of files) {
  const relative=normalize(path.relative(root,file));
  if(sourceRoots.some(p=>relative.startsWith(p+'/'))&&!owner(file)) issues.push({path:relative,code:'unowned_source'});
  if(!/\.(ts|tsx|js|jsx)$/.test(file)) continue;
  const tree=ts.createSourceFile(file,fs.readFileSync(file,'utf8'),ts.ScriptTarget.Latest,true);
  function visit(n) {
    if((ts.isImportDeclaration(n)||ts.isExportDeclaration(n))&&n.moduleSpecifier&&ts.isStringLiteral(n.moduleSpecifier)) edge(file,n.moduleSpecifier.text,n,tree);
    if(ts.isCallExpression(n)&&(n.expression.kind===ts.SyntaxKind.ImportKeyword || n.expression.getText(tree)==='require')) {
      if(n.arguments[0]&&ts.isStringLiteral(n.arguments[0])) edge(file,n.arguments[0].text,n,tree);
      else issues.push({path:relative,code:'computed_module_load'});
    }
    if(ts.isCallExpression(n)&&n.expression.getText(tree)==='import.meta.glob'&&relative!=='app/ui/app/host/contributions.ts') issues.push({path:relative,code:'ambient_discovery'});
    ts.forEachChild(n,visit);
  }
  visit(tree);
}
for(const file of files.filter(p=>p.endsWith('.css'))) {
  const source=fs.readFileSync(file,'utf8');
  const tree=ts.createSourceFile(file,source,ts.ScriptTarget.Latest,true);
  for(const match of source.matchAll(/(?:url\(\s*|@import\s+)["']?(\.\.?\/[^\s"')]+)/g)) edge(file,match[1],tree,tree);
}
console.log(JSON.stringify({status:issues.length?'fail':'pass',issues},null,2));
process.exitCode=issues.length?1:0;
