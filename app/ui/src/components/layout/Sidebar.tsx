'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import { useWorkspaceStore, type WidgetType } from '../../widgets/workspaces';
import {
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Globe,
  Bookmark,
  Activity,
  LineChart,
  AlignJustify,
  Layers,
  ListOrdered,
  Clock,
  Newspaper,
  Database,
  FileSpreadsheet,
  AlertTriangle,
  TrendingUp,
  History,
  BarChart2,
  Sliders,
  FlaskConical,
  PieChart,
  Bot,
  LayoutDashboard,
  GraduationCap,
  Compass,
  Settings,
  type LucideIcon,
} from 'lucide-react';

export interface WidgetItemConfig {
  type?: WidgetType;
  action?: 'settings';
  label: string;
  title?: string;
  symbol?: string;
  icon: LucideIcon;
}

export interface DomainGroupConfig {
  id: string;
  label: string;
  icon: LucideIcon;
  items: WidgetItemConfig[];
}

export const DOMAIN_GROUPS: DomainGroupConfig[] = [
  {
    id: 'data',
    label: 'Data',
    icon: Database,
    items: [
      { type: 'markets', label: 'Markets', title: 'Markets', icon: Globe },
      { type: 'watchlist', label: 'Watchlists', title: 'Watchlists', icon: Bookmark },
      { type: 'marketTicks', label: 'Market Ticks', title: 'Market Ticks', icon: Activity },
      { type: 'market-hours', label: 'Market Hours', title: 'Market Hours', icon: Clock },
      { type: 'news', label: 'News', title: 'News', icon: Newspaper },
      { type: 'data', label: 'Data Explorer', title: 'Data Explorer', icon: Database },
    ],
  },
  {
    id: 'indicators',
    label: 'Indicators',
    icon: LineChart,
    items: [
      { type: 'chart', label: 'Chart', title: 'EURUSD Chart', symbol: 'EURUSD', icon: LineChart },
      { type: 'indicators', label: 'Indicators Studio', title: 'Indicators', icon: TrendingUp },
      { type: 'priceLadder', label: 'Price Ladder', title: 'ESU6 DOM', icon: AlignJustify },
      { type: 'optionsGrid', label: 'Options Grid', title: 'Options Grid', icon: Layers },
    ],
  },
  {
    id: 'strategy',
    label: 'Strategy',
    icon: FileSpreadsheet,
    items: [
      { type: 'strategies', label: 'Strategies', title: 'Strategies', icon: FileSpreadsheet },
    ],
  },
  {
    id: 'risk',
    label: 'Risk',
    icon: AlertTriangle,
    items: [
      { type: 'risk', label: 'Risk Governance', title: 'Risk', icon: AlertTriangle },
    ],
  },
  {
    id: 'trading',
    label: 'Trading',
    icon: TrendingUp,
    items: [
      { type: 'trading', label: 'Trading Cockpit', title: 'Trading', icon: TrendingUp },
      { type: 'positions', label: 'Positions & Orders', title: 'Positions & Orders', icon: ListOrdered },
      { type: 'tradeLog', label: 'Trade Log', title: 'Trade Log', icon: History },
      { type: 'sessions', label: 'Trading Sessions', title: 'Trading Sessions', icon: Clock },
    ],
  },
  {
    id: 'simulation',
    label: 'Simulation',
    icon: History,
    items: [
      { type: 'simulator', label: 'Simulator', title: 'Simulator', icon: History },
    ],
  },
  {
    id: 'analytics',
    label: 'Analytics',
    icon: BarChart2,
    items: [
      { type: 'analytics', label: 'Analytics', title: 'Analytics', icon: BarChart2 },
    ],
  },
  {
    id: 'optimization',
    label: 'Optimization',
    icon: Sliders,
    items: [
      { type: 'optimization', label: 'Optimization', title: 'Optimization', icon: Sliders },
    ],
  },
  {
    id: 'research',
    label: 'Research',
    icon: FlaskConical,
    items: [
      { type: 'research', label: 'Edge Lab', title: 'Edge Lab', icon: FlaskConical },
    ],
  },
  {
    id: 'portfolio',
    label: 'Portfolio',
    icon: PieChart,
    items: [
      { type: 'portfolio', label: 'Portfolio', title: 'Portfolio', icon: PieChart },
    ],
  },
  {
    id: 'agentic',
    label: 'Agentic',
    icon: Bot,
    items: [
      { type: 'agentic', label: 'Agentic Operator', title: 'Agentic Operator', icon: Bot },
    ],
  },
  {
    id: 'resources',
    label: 'Resources',
    icon: LayoutDashboard,
    items: [
      { type: 'dashboard', label: 'Dashboard', title: 'Dashboard', icon: LayoutDashboard },
      { type: 'education', label: 'Education', title: 'Education Resources', icon: GraduationCap },
      { type: 'challenges', label: 'Challenges', title: 'Challenges Dashboard', icon: Compass },
      { type: 'tradePlan', label: 'Trade Plan', title: 'My Trade Plan', icon: FileSpreadsheet },
      { action: 'settings', label: 'System Settings', icon: Settings },
    ],
  },
];

export const Sidebar: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [openDomains, setOpenDomains] = useState<Record<string, boolean>>({
    data: true,
    indicators: true,
    trading: true,
    simulation: true,
    analytics: true,
  });
  const [activeFlyout, setActiveFlyout] = useState<string | null>(null);
  const flyoutRef = useRef<HTMLDivElement | null>(null);

  const { openSettings } = useTradingStore();
  const { addWidgetToWorkspace } = useWorkspaceStore();

  const toggleDomain = (domainId: string) => {
    setOpenDomains((prev) => ({
      ...prev,
      [domainId]: !prev[domainId],
    }));
  };

  const handleItemClick = (item: WidgetItemConfig) => {
    if (item.action === 'settings') {
      openSettings();
    } else if (item.type) {
      addWidgetToWorkspace(item.type, item.title || item.label, item.symbol);
    }
    setActiveFlyout(null);
  };

  // Close flyout on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (flyoutRef.current && !flyoutRef.current.contains(e.target as Node)) {
        setActiveFlyout(null);
      }
    };
    if (activeFlyout) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [activeFlyout]);

  return (
    <aside
      className={`cme-sidebar ${isCollapsed ? 'collapsed' : ''}`}
      aria-label="Sidebar navigation"
    >
      {/* Sidebar Header Toggle */}
      <div
        className="sidebar-toggle-btn"
        onClick={() => {
          setIsCollapsed(!isCollapsed);
          setActiveFlyout(null);
        }}
        data-testid="sidebar-toggle-btn"
        role="button"
        tabIndex={0}
        title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
      >
        {!isCollapsed && <span>HIDE MENU</span>}
        {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </div>

      {/* Domain Groups Container */}
      <div className="sidebar-domains-container" ref={flyoutRef}>
        {DOMAIN_GROUPS.map((domain) => {
          const DomainIcon = domain.icon;
          const isOpen = Boolean(openDomains[domain.id]);
          const isFlyoutOpen = activeFlyout === domain.id;

          if (isCollapsed) {
            return (
              <div
                key={domain.id}
                className={`sidebar-collapsed-domain-wrapper ${isFlyoutOpen ? 'active' : ''}`}
                data-testid={`domain-collapsed-${domain.id}`}
              >
                <div
                  className="sidebar-collapsed-domain-btn"
                  onClick={() => setActiveFlyout(isFlyoutOpen ? null : domain.id)}
                  title={`${domain.label} Widgets`}
                  data-testid={`domain-icon-${domain.id}`}
                  role="button"
                  tabIndex={0}
                >
                  <DomainIcon size={16} />
                </div>

                {/* Collapsed Mode Flyout Dropdown */}
                {isFlyoutOpen && (
                  <div
                    className="sidebar-flyout-menu"
                    data-testid={`flyout-${domain.id}`}
                  >
                    <div className="sidebar-flyout-header">
                      <DomainIcon size={14} />
                      <span>{domain.label.toUpperCase()}</span>
                    </div>
                    <div className="sidebar-flyout-items">
                      {domain.items.map((item) => {
                        const ItemIcon = item.icon;
                        const itemKey = item.type || item.action || item.label;
                        return (
                          <div
                            key={itemKey}
                            className="sidebar-flyout-item"
                            onClick={() => handleItemClick(item)}
                            data-testid={`widget-${itemKey}`}
                            role="button"
                            tabIndex={0}
                          >
                            <ItemIcon size={14} />
                            <span>{item.label}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          }

          return (
            <div
              key={domain.id}
              className={`sidebar-domain-group ${isOpen ? 'open' : 'closed'}`}
              data-testid={`domain-group-${domain.id}`}
            >
              {/* Domain Header / Accordion Toggle */}
              <div
                className={`sidebar-domain-header ${isOpen ? 'active' : ''}`}
                onClick={() => toggleDomain(domain.id)}
                data-testid={`domain-header-${domain.id}`}
                role="button"
                tabIndex={0}
                aria-expanded={isOpen}
              >
                <div className="sidebar-domain-title-left">
                  <DomainIcon size={14} className="sidebar-domain-icon" />
                  <span className="sidebar-domain-title">{domain.label.toUpperCase()}</span>
                </div>
                <ChevronDown
                  size={14}
                  className={`sidebar-domain-chevron ${isOpen ? 'open' : ''}`}
                />
              </div>

              {/* Collapsible Child Widgets */}
              {isOpen && (
                <div
                  className="sidebar-domain-items"
                  data-testid={`domain-items-${domain.id}`}
                >
                  {domain.items.map((item) => {
                    const ItemIcon = item.icon;
                    const itemKey = item.type || item.action || item.label;
                    return (
                      <div
                        key={itemKey}
                        className="sidebar-menu-item sidebar-widget-item"
                        onClick={() => handleItemClick(item)}
                        data-testid={`widget-${itemKey}`}
                        role="button"
                        tabIndex={0}
                        title={`Add ${item.label} widget`}
                      >
                        <ItemIcon size={14} />
                        <span>{item.label}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
};
