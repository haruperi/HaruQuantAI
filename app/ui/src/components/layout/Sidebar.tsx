'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import {
  listWidgetRegistrations,
  useWorkspaceStore,
  type WidgetType,
} from '../../widgets/workspaces';
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

const ICONS: Readonly<Record<string, LucideIcon>> = {
  globe: Globe,
  bookmark: Bookmark,
  activity: Activity,
  'line-chart': LineChart,
  'align-justify': AlignJustify,
  layers: Layers,
  'list-ordered': ListOrdered,
  clock: Clock,
  newspaper: Newspaper,
  database: Database,
  'file-spreadsheet': FileSpreadsheet,
  'alert-triangle': AlertTriangle,
  'trending-up': TrendingUp,
  history: History,
  'bar-chart-2': BarChart2,
  sliders: Sliders,
  'flask-conical': FlaskConical,
  'pie-chart': PieChart,
  bot: Bot,
  'layout-dashboard': LayoutDashboard,
  'graduation-cap': GraduationCap,
  compass: Compass,
};

const DOMAIN_DEFINITIONS = [
  { id: 'data', label: 'Data', icon: Database },
  { id: 'indicators', label: 'Indicators', icon: LineChart },
  { id: 'strategy', label: 'Strategy', icon: FileSpreadsheet },
  { id: 'risk', label: 'Risk', icon: AlertTriangle },
  { id: 'trading', label: 'Trading', icon: TrendingUp },
  { id: 'simulation', label: 'Simulation', icon: History },
  { id: 'analytics', label: 'Analytics', icon: BarChart2 },
  { id: 'optimization', label: 'Optimization', icon: Sliders },
  { id: 'research', label: 'Research', icon: FlaskConical },
  { id: 'portfolio', label: 'Portfolio', icon: PieChart },
  { id: 'agentic', label: 'Agentic', icon: Bot },
  { id: 'resources', label: 'Resources', icon: LayoutDashboard },
] as const;

/** Build current navigation directly from the sole widget registry. */
export function getDomainGroups(): DomainGroupConfig[] {
  const registrations = listWidgetRegistrations();
  return DOMAIN_DEFINITIONS.map((domain) => {
    const items: WidgetItemConfig[] = registrations
      .filter((value) => value.navigation.domain === domain.id)
      .map((value) => ({
        type: value.manifest.widgetType as WidgetType,
        label: value.navigation.label,
        title: value.navigation.title,
        symbol: value.navigation.symbol,
        icon: ICONS[value.navigation.icon] ?? LayoutDashboard,
      }));
    if (domain.id === 'resources') {
      items.push({ action: 'settings', label: 'System Settings', icon: Settings });
    }
    return { ...domain, items };
  });
}

export const Sidebar: React.FC = () => {
  const domainGroups = getDomainGroups();
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
        {domainGroups.map((domain) => {
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
