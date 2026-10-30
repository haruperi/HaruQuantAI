import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  createCodeEditorClient,
  type EditorTabDto,
  type NavigatorItemDto,
  type SearchMatchDto,
  type SyntaxDiagnosticDto,
  type SymbolDto,
  type CompilationDto,
} from './codeEditorClient';

const NO_DIAGNOSTICS: SyntaxDiagnosticDto[] = [];

export function useCodeEditorWorkspace() {
  const client = useMemo(() => createCodeEditorClient(), []);

  // Workspace Tabs & Active Session
  const [tabs, setTabs] = useState<EditorTabDto[]>([]);
  const [activeFilePath, setActiveFilePath] = useState<string | null>(null);
  const [fileContents, setFileContents] = useState<Record<string, string>>({});
  const [cursorPos, setCursorPos] = useState<{ line: number; col: number }>({
    line: 1,
    col: 1,
  });

  const [sessionReady, setSessionReady] = useState(false);
  const [completionSymbols, setCompletionSymbols] = useState<SymbolDto[]>([]);
  const [compilation, setCompilation] = useState<CompilationDto | null>(null);
  useEffect(() => {
    if (compilation?.status === 'COMPLETED') client.symbols().then(setCompletionSymbols).catch(error => setOutputLogs(previous => [`Completion refresh error: ${String(error)}`, ...previous]));
  }, [compilation?.job_id, compilation?.status]);
  const sessionQueue = useRef<Promise<unknown>>(Promise.resolve());
  const documentCommandPending = useRef(false);
  const [isDocumentCommandRunning, setIsDocumentCommandRunning] = useState(false);

  // Navigator Tree
  const [treeRoot, setTreeRoot] = useState<NavigatorItemDto | null>(null);
  const [pathProtection, setPathProtection] = useState<Record<string, boolean>>({});
  const navigatorGeneration = useRef(0);
  const [collapsedFolders, setCollapsedFolders] = useState<Record<string, boolean>>({});
  const [navSearchQuery, setNavSearchQuery] = useState<string>('');
  const [ownershipFilter, setOwnershipFilter] = useState('all');
  const [selectedNavPath, setSelectedNavPath] = useState<string | null>(null);

  // Bottom Dock Tabs
  const [bottomTab, setBottomTab] = useState<'problems' | 'output' | 'results' | 'chart' | 'search' | 'terminal'>(
    'problems',
  );
  const [diagnostics, setDiagnostics] = useState<SyntaxDiagnosticDto[]>([]);
  const [diagnosticFile, setDiagnosticFile] = useState<string | null>(null);
  const [outputLogs, setOutputLogs] = useState<string[]>([
    `[${new Date().toLocaleTimeString()}] Python Extension Runtime ready (3.14.7).`,
    `[${new Date().toLocaleTimeString()}] Snippets repository loaded at app/include/.`,
  ]);
  const [searchResults, setSearchResults] = useState<SearchMatchDto[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchOptions, setSearchOptions] = useState({ caseSensitive: false, regex: false, wholeWord: false, searchDir: '' });

  // Modals
  const [showTemplateModal, setShowTemplateModal] = useState<boolean>(false);
  const [showTesterModal, setShowTesterModal] = useState<boolean>(false);
  const [showImportExportModal, setShowImportExportModal] = useState<boolean>(false);

  // Context Menu State
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    item: NavigatorItemDto;
  } | null>(null);

  // Load initial workspace state & navigator
  const refreshNavigator = async () => {
    const generation = ++navigatorGeneration.current;
    try {
      const tree = await client.fetchNavigator(undefined, ownershipFilter);
      const protection: Record<string, boolean> = {};
      const visit = (item: NavigatorItemDto) => { if (item.protected !== undefined) protection[item.id] = item.protected; item.children?.forEach(visit); };
      visit(tree);
      setPathProtection(previous => ({ ...previous, ...protection }));
      if (generation === navigatorGeneration.current) setTreeRoot(tree);
    } catch (error) {
      setOutputLogs((prev) => [`Navigator error: ${String(error)}`, ...prev]);
    }
  };

  useEffect(() => { void refreshNavigator(); }, [ownershipFilter]);

  useEffect(() => {
    let active = true;
    refreshNavigator();
    client.symbols().then(value => { if (active) setCompletionSymbols(value); }).catch(error => { if (active) setOutputLogs(previous => [`Completion catalogue error: ${String(error)}`, ...previous]); });
    client
      .initWorkspace()
      .then((init) => {
        if (!active) return;
        setSessionReady(true);
        if (init.recovery_warnings?.length) {
          setOutputLogs(previous => [...init.recovery_warnings!, ...previous]);
          setBottomTab('output');
        }
        if (init.open_tabs && init.open_tabs.length > 0) {
          setTabs(init.open_tabs);
          setActiveFilePath(init.active_file || init.open_tabs[0].file_path);
          const contents: Record<string, string> = {};
          init.open_tabs.forEach((t) => {
            contents[t.file_path] = t.content;
          });
          setFileContents(contents);
        }
      })
      .catch((error) => { if (active) { setOutputLogs((prev) => [`Session error: ${String(error)}`, ...prev]); setBottomTab('output'); } });
    return () => { active = false; };
  }, []);

  const activeTab = tabs.find((t) => t.file_path === activeFilePath) || tabs[0];
  const activeContent = activeFilePath ? (fileContents[activeFilePath] ?? activeTab?.content ?? '') : '';
  const findProtected = (item: NavigatorItemDto | null): boolean => Boolean(item && ((item.id === activeFilePath && item.protected) || item.children?.some(child => findProtected(child))));
  const activeProtected = activeFilePath && pathProtection[activeFilePath] !== undefined ? pathProtection[activeFilePath] : findProtected(treeRoot);

  useEffect(() => {
    if (!sessionReady || documentCommandPending.current) return;
    sessionQueue.current = sessionQueue.current.catch(() => {}).then(() => client.syncSession(tabs, activeFilePath));
    sessionQueue.current.catch((error) => setOutputLogs((prev) => [`Session save error: ${String(error)}`, ...prev]));
  }, [tabs, activeFilePath, sessionReady, client, isDocumentCommandRunning]);

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (tabs.some((tab) => tab.is_dirty)) {
        event.preventDefault();
        event.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [tabs]);

  // Tab & File actions
  const handleOpenPath = async (filePath: string) => {
    if (documentCommandPending.current) return;
    try {
      await sessionQueue.current;
      if (tabs.some((tab) => tab.file_path === filePath)) {
        setActiveFilePath(filePath);
        return;
      }
      const res = await client.openTab(filePath);
      if (!tabs.some((t) => t.file_path === res.tab.file_path)) {
        setTabs((prev) => [...prev, res.tab]);
      }
      setFileContents((prev) => ({
        ...prev,
        [res.tab.file_path]: res.tab.content,
      }));
      setActiveFilePath(res.tab.file_path);
      setSelectedNavPath(res.tab.file_path);
    } catch (error) {
      setOutputLogs((prev) => [`Open error: ${String(error)}`, ...prev]);
    }
  };

  const handleCloseTab = async (filePath: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (documentCommandPending.current) return;
    const tab = tabs.find((item) => item.file_path === filePath);
    if (tab?.is_dirty && !confirm(`Discard unsaved changes in ${tab.title}?`)) return;
    try {
      await sessionQueue.current;
      const result = await client.closeTab(filePath, Boolean(tab?.is_dirty));
      if (result.status === 'unsaved_changes') return;
    } catch (error) {
      setOutputLogs((prev) => [`Close error: ${String(error)}`, ...prev]);
      return;
    }
    const newTabs = tabs.filter((t) => t.file_path !== filePath);
    setTabs(newTabs);
    if (activeFilePath === filePath) {
      setActiveFilePath(newTabs.length > 0 ? newTabs[newTabs.length - 1].file_path : null);
    }
  };

  const handleContentChange = (content: string) => {
    if (!activeFilePath || documentCommandPending.current || activeProtected) return;
    setFileContents((prev) => ({ ...prev, [activeFilePath]: content }));
    setTabs((prev) => prev.map((t) => (t.file_path === activeFilePath ? { ...t, is_dirty: true, content } : t)));
  };

  const handleSave = async () => {
    if (!activeFilePath || documentCommandPending.current) return;
    try {
      await sessionQueue.current;
      const res = await client.saveFile(activeFilePath, activeContent);
      setTabs((prev) => prev.map((t) => (t.file_path === activeFilePath ? { ...t, is_dirty: false } : t)));
      setDiagnostics(res.diagnostics || []);
      setDiagnosticFile(activeFilePath);
      setOutputLogs((prev) => [
        `[${new Date().toLocaleTimeString()}] Saved ${activeFilePath} (${activeContent.length} chars). Diagnostics: ${res.diagnostics?.length || 0}`,
        ...prev,
      ]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Save failed';
      setOutputLogs((prev) => [`[${new Date().toLocaleTimeString()}] Save error: ${msg}`, ...prev]);
    }
  };

  const handleSaveAs = async () => {
    if (!activeFilePath || documentCommandPending.current) return;
    const target = prompt('Save As path:', activeFilePath.replace(/(\.[^/.]+)?$/, '_copy$1'));
    if (!target) return;
    const source = activeFilePath;
    const content = activeContent;
    documentCommandPending.current = true;
    setIsDocumentCommandRunning(true);
    try {
      const operation = sessionQueue.current.then(() => client.saveAsFile(source, target, content));
      sessionQueue.current = operation;
      const result = await operation;
      setTabs((previous) => previous.map((tab) => tab.file_path === result.source_path ? result.tab : tab));
      setFileContents((previous) => {
        const updated = { ...previous };
        delete updated[result.source_path];
        updated[result.file_path] = result.tab.content;
        return updated;
      });
      setActiveFilePath(result.active_file);
      setSelectedNavPath(result.file_path);
      setDiagnostics(result.diagnostics);
      setDiagnosticFile(result.file_path);
      setOutputLogs((previous) => [`Saved As ${result.file_path} (${result.bytes_written} bytes).`, ...previous]);
      void refreshNavigator();
    } catch (error) {
      setOutputLogs((previous) => [`Save As error: ${String(error)}`, ...previous]);
      setBottomTab('output');
    } finally {
      documentCommandPending.current = false;
      setIsDocumentCommandRunning(false);
    }
  };

  const handleSaveAll = async () => {
    if (documentCommandPending.current) return;
    const dirtyFiles = tabs
      .filter((t) => t.is_dirty)
      .map((t) => ({
        file_path: t.file_path,
        content: fileContents[t.file_path] ?? t.content,
      }));
    if (dirtyFiles.length === 0) return;
    try {
      await sessionQueue.current;
      await client.saveAllFiles(dirtyFiles);
      setTabs((prev) => prev.map((t) => ({ ...t, is_dirty: false })));
      setOutputLogs((prev) => [
        `[${new Date().toLocaleTimeString()}] Saved all ${dirtyFiles.length} open dirty file(s).`,
        ...prev,
      ]);
    } catch (error) {
      setOutputLogs((prev) => [`Save All error: ${String(error)}`, ...prev]);
    }
  };

  const handleReload = async () => {
    if (!activeFilePath || documentCommandPending.current) return;
    if (activeTab?.is_dirty && !confirm('Discard unsaved changes and reload from disk?')) return;
    documentCommandPending.current = true;
    setIsDocumentCommandRunning(true);
    try {
      await sessionQueue.current;
      const result = await client.reloadDisk(activeFilePath, Boolean(activeTab?.is_dirty));
      setTabs(previous => previous.map(tab => tab.file_path === result.tab.file_path ? result.tab : tab));
      setFileContents(previous => ({ ...previous, [result.tab.file_path]: result.tab.content }));
      setDiagnostics([]);
      setDiagnosticFile(null);
    } catch (error) {
      setOutputLogs(previous => [`Reload error: ${String(error)}`, ...previous]);
      setBottomTab('output');
    } finally {
      documentCommandPending.current = false;
      setIsDocumentCommandRunning(false);
    }
  };

  const handleCompile = async () => {
    if (!activeFilePath || documentCommandPending.current) return;
    if (compilation && !['COMPLETED', 'FAILED', 'CANCELLED', 'INTERRUPTED'].includes(compilation.status)) return;
    setOutputLogs((prev) => [
      `[${new Date().toLocaleTimeString()}] Starting AST syntax validation for ${activeFilePath}...`,
      ...prev,
    ]);
    try {
      const snapshot = await client.startCompilation('file', activeFilePath, activeContent);
      setCompilation(snapshot);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Compilation error';
      setOutputLogs((prev) => [`[${new Date().toLocaleTimeString()}] ✗ Error: ${msg}`, ...prev]);
      setBottomTab('problems');
    }
  };

  const handleSearchInFiles = async () => {
    if (!searchQuery.trim()) return;
    try {
      const matches = await client.searchFiles(searchQuery.trim(), { ...searchOptions, searchDir: searchOptions.searchDir || undefined });
      setSearchResults(matches);
      setBottomTab('search');
    } catch (error) {
      setOutputLogs((prev) => [`Search error: ${String(error)}`, ...prev]);
      setBottomTab('output');
    }
  };

  // Keyboard shortcuts (Ctrl+S, F7)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        handleSave();
      } else if (e.key === 'F7') {
        e.preventDefault();
        handleCompile();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeFilePath, activeContent, compilation?.status, isDocumentCommandRunning]);

  // Document & Outline Parsers
  const outlineSymbols = useMemo(() => {
    const lines = activeContent.split('\n');
    const classes: Array<{
      name: string;
      inherits?: string;
      methods: string[];
      attrs: string[];
    }> = [];
    const imports: string[] = [];
    let currentClass: {
      name: string;
      inherits?: string;
      methods: string[];
      attrs: string[];
    } | null = null;

    lines.forEach((line) => {
      const trim = line.trim();
      if (trim.startsWith('import ') || trim.startsWith('from ')) {
        imports.push(trim);
      }
      const classMatch = trim.match(/^class\s+([A-Za-z0-9_]+)(?:\(([^)]+)\))?:/);
      if (classMatch) {
        currentClass = {
          name: classMatch[1],
          inherits: classMatch[2],
          methods: [],
          attrs: [],
        };
        classes.push(currentClass);
      } else if (currentClass && trim.startsWith('def ')) {
        const defMatch = trim.match(/^def\s+([A-Za-z0-9_]+)\s*\(([^)]*)\):/);
        if (defMatch) {
          currentClass.methods.push(`${defMatch[1]}(${defMatch[2].replace(/self,?\s*/, '')})`);
        }
      } else if (currentClass && /^[a-z_][a-z0-9_]*\s*:\s*[A-Za-z0-9_\[\]]+(?:\s*=.*)?$/.test(trim)) {
        currentClass.attrs.push(trim.split(':')[0].trim());
      }
    });

    return { classes, imports };
  }, [activeContent]);

  // Context Menu Actions
  const handleContextMenuAction = async (action: string) => {
    if (documentCommandPending.current) return;
    if (!contextMenu && !['new_file', 'new_dir'].includes(action)) return;
    const item = contextMenu?.item ?? { id: 'app/include', name: 'snippets', type: 'directory' as const };
    setContextMenu(null);

    if (action === 'open') {
      if (item.type === 'file') handleOpenPath(item.id);
    } else if (action === 'new_file') {
      const fileName = prompt('Enter new file name:', 'custom_snippet.py');
      if (fileName) {
        const target =
          item.type === 'directory' ? `${item.id}/${fileName}` : `${item.id.replace(/\/[^/]+$/, '')}/${fileName}`;
        await client.newFile(target, '# New snippet\n');
        refreshNavigator();
        handleOpenPath(target);
      }
    } else if (action === 'new_dir') {
      const dirName = prompt('Enter new directory name:', 'new_folder');
      if (dirName) {
        const target =
          item.type === 'directory' ? `${item.id}/${dirName}` : `${item.id.replace(/\/[^/]+$/, '')}/${dirName}`;
        await client.newDir(target);
        refreshNavigator();
      }
    } else if (action === 'clone') {
      const info = await client.pathInfo(item.id);
      const target = prompt('Clone to path:', info.clone_target);
      if (target) {
        await client.cloneFile(item.id, target);
        refreshNavigator();
        handleOpenPath(target);
      }
    } else if (action === 'rename') {
      const newPath = prompt('Rename path to:', item.id);
      if (newPath && newPath !== item.id) {
        await sessionQueue.current;
        await client.renameFile(item.id, newPath);
        const remap = (path: string) =>
          path === item.id || path.startsWith(item.id + '/') ? newPath + path.slice(item.id.length) : path;
        setTabs((prev) =>
          prev.map((tab) => ({
            ...tab,
            file_path: remap(tab.file_path),
            title: remap(tab.file_path).split('/').pop()!,
          })),
        );
        setFileContents((prev) =>
          Object.fromEntries(Object.entries(prev).map(([path, content]) => [remap(path), content])),
        );
        setActiveFilePath((prev) => (prev ? remap(prev) : prev));
        refreshNavigator();
      }
    } else if (action === 'delete') {
      if (confirm(`Delete ${item.name}?`)) {
        await sessionQueue.current;
        await client.deleteFile(item.id);
        const remaining = tabs.filter((tab) => tab.file_path !== item.id && !tab.file_path.startsWith(item.id + '/'));
        setTabs(remaining);
        if (!remaining.some((tab) => tab.file_path === activeFilePath))
          setActiveFilePath(remaining[0]?.file_path ?? null);
        refreshNavigator();
      }
    } else if (action === 'compile') {
      handleCompile();
    } else if (action === 'test') {
      setShowTesterModal(true);
    } else if (action === 'copy_path') {
      navigator.clipboard.writeText(item.id);
    }
  };

  // Close context menu on outside click
  useEffect(() => {
    const handleOutsideClick = () => setContextMenu(null);
    window.addEventListener('click', handleOutsideClick);
    return () => window.removeEventListener('click', handleOutsideClick);
  }, []);

  // Line numbers calculation
  const linesCount = activeContent.split('\n').length || 1;

  return {
    tabs,
    activeFilePath,
    setActiveFilePath: (path: string | null) => {
      if (!documentCommandPending.current) setActiveFilePath(path);
    },
    isDocumentCommandRunning,
    activeProtected,
    completionSymbols,
    compilation,
    setCompilation,
    cursorPos,
    setCursorPos,
    treeRoot,
    collapsedFolders,
    setCollapsedFolders,
    navSearchQuery,
    ownershipFilter,
    setOwnershipFilter,
    setNavSearchQuery,
    selectedNavPath,
    bottomTab,
    setBottomTab,
    diagnostics: diagnosticFile === activeFilePath ? diagnostics : NO_DIAGNOSTICS,
    outputLogs,
    setOutputLogs,
    searchResults,
    searchQuery,
    searchOptions,
    setSearchOptions,
    setSearchQuery,
    showTemplateModal,
    setShowTemplateModal,
    showTesterModal,
    setShowTesterModal,
    showImportExportModal,
    setShowImportExportModal,
    contextMenu,
    setContextMenu,
    refreshNavigator,
    activeTab,
    activeContent,
    handleOpenPath,
    handleCloseTab,
    handleContentChange,
    handleSave,
    handleSaveAs,
    handleReload,
    publishDiagnostics: (file: string, errors: SyntaxDiagnosticDto[]) => { setDiagnosticFile(file); setDiagnostics(errors); },
    handleSaveAll,
    handleCompile,
    handleSearchInFiles,
    outlineSymbols,
    handleContextMenuAction,
  };
}

export type CodeEditorState = ReturnType<typeof useCodeEditorWorkspace>;
