import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  createCodeEditorClient,
  type CompileResultDto,
  type EditorTabDto,
  type NavigatorItemDto,
  type SearchMatchDto,
  type SyntaxDiagnosticDto,
} from './codeEditorClient';

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
  const sessionQueue = useRef<Promise<unknown>>(Promise.resolve());

  // Navigator Tree
  const [treeRoot, setTreeRoot] = useState<NavigatorItemDto | null>(null);
  const [collapsedFolders, setCollapsedFolders] = useState<Record<string, boolean>>({});
  const [navSearchQuery, setNavSearchQuery] = useState<string>('');
  const [selectedNavPath, setSelectedNavPath] = useState<string | null>(null);

  // Bottom Dock Tabs
  const [bottomTab, setBottomTab] = useState<'problems' | 'output' | 'results' | 'chart' | 'search' | 'terminal'>(
    'problems',
  );
  const [diagnostics, setDiagnostics] = useState<SyntaxDiagnosticDto[]>([]);
  const [outputLogs, setOutputLogs] = useState<string[]>([
    `[${new Date().toLocaleTimeString()}] Python Extension Runtime ready (3.14.7).`,
    `[${new Date().toLocaleTimeString()}] Snippets repository loaded at app/include/.`,
  ]);
  const [searchResults, setSearchResults] = useState<SearchMatchDto[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');

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
  const editorTextareaRef = useRef<HTMLTextAreaElement>(null);

  // Load initial workspace state & navigator
  const refreshNavigator = async () => {
    try {
      const tree = await client.fetchNavigator();
      setTreeRoot(tree);
    } catch (error) {
      setOutputLogs((prev) => [`Navigator error: ${String(error)}`, ...prev]);
    }
  };

  useEffect(() => {
    refreshNavigator();
    client
      .initWorkspace()
      .then((init) => {
        setSessionReady(true);
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
      .catch((error) => setOutputLogs((prev) => [`Session error: ${String(error)}`, ...prev]));
  }, []);

  const activeTab = tabs.find((t) => t.file_path === activeFilePath) || tabs[0];
  const activeContent = activeFilePath ? (fileContents[activeFilePath] ?? activeTab?.content ?? '') : '';

  useEffect(() => {
    if (!sessionReady) return;
    sessionQueue.current = sessionQueue.current.catch(() => {}).then(() => client.syncSession(tabs, activeFilePath));
    sessionQueue.current.catch((error) => setOutputLogs((prev) => [`Session save error: ${String(error)}`, ...prev]));
  }, [tabs, activeFilePath, sessionReady, client]);

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
    if (!activeFilePath) return;
    setFileContents((prev) => ({ ...prev, [activeFilePath]: content }));
    setTabs((prev) => prev.map((t) => (t.file_path === activeFilePath ? { ...t, is_dirty: true, content } : t)));
  };

  const handleSave = async () => {
    if (!activeFilePath) return;
    try {
      await sessionQueue.current;
      const res = await client.saveFile(activeFilePath, activeContent);
      setTabs((prev) => prev.map((t) => (t.file_path === activeFilePath ? { ...t, is_dirty: false } : t)));
      setDiagnostics(res.diagnostics || []);
      setOutputLogs((prev) => [
        `[${new Date().toLocaleTimeString()}] Saved ${activeFilePath} (${activeContent.length} chars). Diagnostics: ${res.diagnostics?.length || 0}`,
        ...prev,
      ]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Save failed';
      setOutputLogs((prev) => [`[${new Date().toLocaleTimeString()}] Save error: ${msg}`, ...prev]);
    }
  };

  const handleSaveAll = async () => {
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

  const handleCompile = async () => {
    if (!activeFilePath) return;
    setOutputLogs((prev) => [
      `[${new Date().toLocaleTimeString()}] Starting AST syntax validation for ${activeFilePath}...`,
      ...prev,
    ]);
    try {
      const res = await client.compileFile(activeFilePath, activeContent);
      setDiagnostics(res.errors || []);
      if (res.success) {
        setOutputLogs((prev) => [
          `[${new Date().toLocaleTimeString()}] ✓ AST Syntax Check Passed. Module reloaded dynamically.`,
          `[${new Date().toLocaleTimeString()}] Compilation successful (0 errors, 0 warnings).`,
          ...prev,
        ]);
        setBottomTab('output');
      } else {
        setOutputLogs((prev) => [
          `[${new Date().toLocaleTimeString()}] ✗ Compilation failed with ${res.errors?.length || 1} error(s).`,
          ...prev,
        ]);
        setBottomTab('problems');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Compilation error';
      setOutputLogs((prev) => [`[${new Date().toLocaleTimeString()}] ✗ Error: ${msg}`, ...prev]);
      setBottomTab('problems');
    }
  };

  const handleSearchInFiles = async () => {
    if (!searchQuery.trim()) return;
    try {
      const matches = await client.searchFiles(searchQuery.trim());
      setSearchResults(matches);
      setBottomTab('search');
    } catch (error) {
      setOutputLogs((prev) => [`Search error: ${String(error)}`, ...prev]);
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
  }, [activeFilePath, activeContent]);

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
      const target = prompt('Clone to path:', `${item.id.replace(/\.py$/, '')}_clone.py`);
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
  const lineNumbers = Array.from({ length: linesCount }, (_, i) => i + 1);

  return {
    tabs,
    activeFilePath,
    setActiveFilePath,
    cursorPos,
    setCursorPos,
    treeRoot,
    collapsedFolders,
    setCollapsedFolders,
    navSearchQuery,
    setNavSearchQuery,
    selectedNavPath,
    bottomTab,
    setBottomTab,
    diagnostics,
    outputLogs,
    setOutputLogs,
    searchResults,
    searchQuery,
    setSearchQuery,
    showTemplateModal,
    setShowTemplateModal,
    showTesterModal,
    setShowTesterModal,
    showImportExportModal,
    setShowImportExportModal,
    contextMenu,
    setContextMenu,
    editorTextareaRef,
    refreshNavigator,
    activeTab,
    activeContent,
    handleOpenPath,
    handleCloseTab,
    handleContentChange,
    handleSave,
    handleSaveAll,
    handleCompile,
    handleSearchInFiles,
    outlineSymbols,
    handleContextMenuAction,
    lineNumbers,
  };
}

export type CodeEditorState = ReturnType<typeof useCodeEditorWorkspace>;
