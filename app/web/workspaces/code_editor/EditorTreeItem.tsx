import React from 'react';
import { ChevronRight, ChevronDown, Folder, FileCode } from 'lucide-react';
import type { NavigatorItemDto } from './codeEditorClient';

// Subcomponent: Recursive Tree Item
interface RenderTreeItemProps {
  item: NavigatorItemDto;
  collapsed: Record<string, boolean>;
  selectedPath: string | null;
  searchQuery: string;
  onToggle: (path: string) => void;
  onSelectFile: (path: string) => void;
  onContextMenu: (e: React.MouseEvent, item: NavigatorItemDto) => void;
}

export function RenderTreeItem({
  item,
  collapsed,
  selectedPath,
  searchQuery,
  onToggle,
  onSelectFile,
  onContextMenu,
}: RenderTreeItemProps) {
  const isDir = item.type === 'directory';
  const isCollapsed = collapsed[item.id] ?? false;
  const isSelected = selectedPath === item.id;
  const parts = item.id.replaceAll('\\', '/').split('/');
  const domains: Record<string, string> = {
    indicators: 'Indicator',
    actions: 'Action',
    comparisons: 'Condition',
    functions: 'Function',
    signals: 'Signal',
    orders: 'Order',
    metrics: 'Metric',
    trade_columns: 'Trade',
    money_management: 'Sizing',
    monte_carlo: 'Monte Carlo',
    what_if: 'What-if',
    analysis: 'Analysis',
    ai_tools: 'AI tool',
    checker: 'Checker',
    code: 'Code',
    columns: 'Columns',
    correlation_of: 'Correlation',
    custom_analysis: 'Analysis',
    engine_charts: 'Charts',
    formulas: 'Formulas',
    negater: 'Negater',
    portfolio_master_fitness: 'Fitness',
    stats: 'Stats',
    trade_analysis: 'Trade Analysis',
  };
  const domainIndex = parts[2] === 'blocks' ? 3 : 2;
  const badge =
    parts[0] === 'app' && (parts[1] === 'extend' || parts[1] === 'include')
      ? parts[domainIndex] === 'indicators' && parts[domainIndex + 1] && (isDir || parts.length > domainIndex + 2)
        ? parts[domainIndex + 1]
        : domains[parts[domainIndex]]
      : undefined;

  // Filter matching
  if (searchQuery && !item.name.toLowerCase().includes(searchQuery.toLowerCase())) {
    const hasMatchingChild = (node: NavigatorItemDto): boolean => {
      if (node.name.toLowerCase().includes(searchQuery.toLowerCase())) return true;
      return node.children ? node.children.some(hasMatchingChild) : false;
    };
    if (!hasMatchingChild(item)) return null;
  }

  return (
    <div>
      <div
        onClick={() => {
          if (isDir) onToggle(item.id);
          else onSelectFile(item.id);
        }}
        onContextMenu={(e) => onContextMenu(e, item)}
        className={`flex items-center gap-1.5 py-1 px-1.5 rounded cursor-pointer transition-colors ${
          isSelected ? 'bg-blue-600/20 text-blue-300 font-semibold' : 'hover:bg-slate-800/60 text-slate-300'
        }`}
      >
        {isDir ? (
          <>
            {isCollapsed ? (
              <ChevronRight className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
            )}
            <Folder className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
          </>
        ) : (
          <FileCode className="w-3.5 h-3.5 text-blue-400 ml-4 flex-shrink-0" />
        )}
        <span className="truncate">{item.name}</span>
        {item.ownership && <span className="text-[9px] text-slate-500">{item.ownership}{item.protected ? ' · protected' : ''}</span>}
        {badge && (
          <span
            title="Building block domain"
            className="ml-auto px-1 rounded text-[9px] text-slate-400 border border-slate-800"
          >
            {badge}
          </span>
        )}
      </div>

      {isDir && !isCollapsed && item.children && (
        <div className="pl-3.5 border-l border-slate-800/60 ml-2">
          {item.children.map((child) => (
            <RenderTreeItem
              key={child.id}
              item={child}
              collapsed={collapsed}
              selectedPath={selectedPath}
              searchQuery={searchQuery}
              onToggle={onToggle}
              onSelectFile={onSelectFile}
              onContextMenu={onContextMenu}
            />
          ))}
        </div>
      )}
    </div>
  );
}
