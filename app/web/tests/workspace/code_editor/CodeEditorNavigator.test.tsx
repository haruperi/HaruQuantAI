import React from 'react';
import { renderToString } from 'react-dom/server';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { NavigatorItemDto } from '../../../workspaces/code_editor/codeEditorClient';
import { RenderTreeItem } from '../../../workspaces/code_editor/EditorTreeItem';
import { CodeEditorWorkspace } from '../../../workspaces/code_editor/CodeEditorWorkspace';

const mockWorkspaceState = {
  tabs: [],
  activeFilePath: null,
  setActiveFilePath: vi.fn(),
  cursorPos: { line: 1, col: 1 },
  setCursorPos: vi.fn(),
  treeRoot: null as NavigatorItemDto | null,
  collapsedFolders: {},
  setCollapsedFolders: vi.fn(),
  navSearchQuery: '',
  setNavSearchQuery: vi.fn(),
  selectedNavPath: null,
  bottomTab: 'output' as const,
  setBottomTab: vi.fn(),
  diagnostics: [],
  outputLogs: [],
  setOutputLogs: vi.fn(),
  searchResults: [],
  searchQuery: '',
  setSearchQuery: vi.fn(),
  showTemplateModal: false,
  setShowTemplateModal: vi.fn(),
  showTesterModal: false,
  setShowTesterModal: vi.fn(),
  showImportExportModal: false,
  setShowImportExportModal: vi.fn(),
  contextMenu: null,
  setContextMenu: vi.fn(),
  editorTextareaRef: { current: null },
  refreshNavigator: vi.fn(),
  activeTab: undefined,
  activeContent: '',
  handleOpenPath: vi.fn(),
  handleCloseTab: vi.fn(),
  handleContentChange: vi.fn(),
  handleSave: vi.fn(),
  handleSaveAll: vi.fn(),
  handleCompile: vi.fn(),
  handleSearchInFiles: vi.fn(),
  outlineSymbols: { classes: [], imports: [] },
  handleContextMenuAction: vi.fn(),
  lineNumbers: [1],
  searchOptions: { caseSensitive: false, wholeWord: false, regex: false, searchDir: '' },
  setSearchOptions: vi.fn(),
  compilation: null,
  diagnosticFile: null,
  pathProtection: {},
  activeProtected: false,
  isDocumentCommandRunning: false,
  completionSymbols: { classes: [], functions: [] },
  ownershipFilter: 'all' as const,
  setOwnershipFilter: vi.fn(),
  sessionReady: true,
  handleSaveAs: vi.fn(),
  handleRevert: vi.fn(),
  formatCode: vi.fn(),
  activeLineIndex: 0,
};

vi.mock('../../../workspaces/code_editor/useCodeEditorWorkspace', () => ({
  useCodeEditorWorkspace: () => mockWorkspaceState,
}));

describe('CodeEditor Navigator Tree Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('unwraps extend root directory and renders child folders directly at root level', () => {
    mockWorkspaceState.treeRoot = {
      id: 'app/extend',
      name: 'extend',
      type: 'directory',
      ownership: 'user',
      protected: true,
      children: [
        {
          id: 'app/extend/ai_tools',
          name: 'ai_tools',
          type: 'directory',
          ownership: 'user',
          protected: false,
          children: [],
        },
        {
          id: 'app/extend/blocks',
          name: 'blocks',
          type: 'directory',
          ownership: 'user',
          protected: true,
          children: [],
        },
        {
          id: 'app/extend/strategies',
          name: 'strategies',
          type: 'directory',
          ownership: 'user',
          protected: true,
          children: [],
        },
        {
          id: 'app/extend/trading',
          name: 'trading',
          type: 'directory',
          ownership: 'user',
          protected: true,
          children: [],
        },
      ],
    };

    const html = renderToString(<CodeEditorWorkspace />);

    // Child folders must be rendered
    expect(html).toContain('ai_tools');
    expect(html).toContain('blocks');
    expect(html).toContain('strategies');
    expect(html).toContain('trading');

    // The outer 'extend' directory item itself should not be rendered as a tree item label
    expect(html).not.toContain('<span class="truncate">extend</span>');
  });

  it('renders placeholder when extend directory has no children', () => {
    mockWorkspaceState.treeRoot = {
      id: 'app/extend',
      name: 'extend',
      type: 'directory',
      ownership: 'user',
      protected: true,
      children: [],
    };

    const html = renderToString(<CodeEditorWorkspace />);
    expect(html).toContain('No snippets found');
  });

  it('renders non-extend root directories normally', () => {
    mockWorkspaceState.treeRoot = {
      id: 'app/extend/strategies',
      name: 'strategies',
      type: 'directory',
      ownership: 'user',
      protected: true,
      children: [
        {
          id: 'app/extend/strategies/my_strat.py',
          name: 'my_strat.py',
          type: 'file',
          ownership: 'user',
          protected: false,
        },
      ],
    };

    const html = renderToString(<CodeEditorWorkspace />);
    expect(html).toContain('<span class="truncate">strategies</span>');
    expect(html).toContain('my_strat.py');
  });

  it('renders RenderTreeItem with appropriate domain badges for extend subfolders', () => {
    const aiToolsItem: NavigatorItemDto = {
      id: 'app/extend/ai_tools',
      name: 'ai_tools',
      type: 'directory',
      ownership: 'user',
      children: [],
    };
    const html = renderToString(
      <RenderTreeItem
        item={aiToolsItem}
        collapsed={{}}
        selectedPath={null}
        searchQuery=""
        onToggle={vi.fn()}
        onSelectFile={vi.fn()}
        onContextMenu={vi.fn()}
      />
    );

    expect(html).toContain('ai_tools');
    expect(html).toContain('AI tool');
  });
});
