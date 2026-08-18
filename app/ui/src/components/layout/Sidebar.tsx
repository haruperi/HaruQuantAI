'use client';

import React, { useState } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import { useWorkspaceStore, type WidgetType } from '../../features/workspaces';
import {
  ChevronLeft,
  ChevronRight,
  Globe,
  Bookmark,
  LineChart,
  AlignJustify,
  Layers,
  ListOrdered,
  MessageSquare,
  Calendar as CalendarIcon,
  Newspaper,
  Compass,
  GraduationCap,
  FileSpreadsheet,
  History,
  LayoutDashboard,
  FlaskConical,
  TrendingUp,
  AlertTriangle,
  PieChart,
  Settings,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { openSettings } = useTradingStore();
  const { addWidgetToWorkspace } = useWorkspaceStore();

  const handleAddWidget = (type: string, title: string) => {
    addWidgetToWorkspace(type as WidgetType, title);
  };

  return (
    <aside className={`cme-sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      {/* Sidebar Header Toggle */}
      <div className="sidebar-toggle-btn" onClick={() => setIsCollapsed(!isCollapsed)}>
        {!isCollapsed && <span>HIDE MENU</span>}
        {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </div>

      {/* Section 1: ADD WIDGETS */}
      <div className="sidebar-section">
        {!isCollapsed && <div className="sidebar-section-title">ADD WIDGETS</div>}

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('markets', 'Markets')}>
          <Globe size={15} />
          {!isCollapsed && <span>Markets</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('watchlist', 'Watchlists')}>
          <Bookmark size={15} />
          {!isCollapsed && <span>Watchlists</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('chart', 'EURUSD Chart')}>
          <LineChart size={15} />
          {!isCollapsed && <span>Chart</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('priceLadder', 'ESU6 DOM')}>
          <AlignJustify size={15} />
          {!isCollapsed && <span>Price Ladder</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('optionsGrid', 'Options Grid')}>
          <Layers size={15} />
          {!isCollapsed && <span>Options</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('positions', 'Positions & Orders')}>
          <ListOrdered size={15} />
          {!isCollapsed && <span>Positions</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('positions', 'Orders Window')}>
          <ListOrdered size={15} />
          {!isCollapsed && <span>Orders</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('commentary', 'Commentary')}>
          <MessageSquare size={15} />
          {!isCollapsed && <span>Commentary</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('calendar', 'Calendar')}>
          <CalendarIcon size={15} />
          {!isCollapsed && <span>Calendar</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('commentary', 'News')}>
          <Newspaper size={15} />
          {!isCollapsed && <span>News</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('dashboard', 'Dashboard')}>
          <LayoutDashboard size={15} />
          {!isCollapsed && <span>Dashboard</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('strategies', 'Strategies')}>
          <FileSpreadsheet size={15} />
          {!isCollapsed && <span>Strategies</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('research', 'Edge Lab')}>
          <FlaskConical size={15} />
          {!isCollapsed && <span>Edge Lab</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('optimization', 'Optimization')}>
          <FlaskConical size={15} />
          {!isCollapsed && <span>Optimization</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('portfolio', 'Portfolio')}>
          <PieChart size={15} />
          {!isCollapsed && <span>Portfolio</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('agentic', 'Agentic Operator')}>
          <span>Agentic Operator</span>
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('simulator', 'Simulator')}>
          <History size={15} />
          {!isCollapsed && <span>Simulator</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('risk', 'Risk')}>
          <AlertTriangle size={15} />
          {!isCollapsed && <span>Risk</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('trading', 'Trading')}>
          <TrendingUp size={15} />
          {!isCollapsed && <span>Trading</span>}
        </div>
        <div className="sidebar-menu-item" onClick={() => handleAddWidget('sessions', 'Trading Sessions')}>
          {!isCollapsed && <span>Sessions</span>}
        </div>
      </div>

      {/* Section 2: CHALLENGE */}
      <div className="sidebar-section">
        {!isCollapsed && <div className="sidebar-section-title">CHALLENGE</div>}

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('challenges', 'Challenges Dashboard')}>
          <Compass size={15} />
          {!isCollapsed && <span>Discover</span>}
        </div>
      </div>

      {/* Section 3: RESOURCES */}
      <div className="sidebar-section">
        {!isCollapsed && <div className="sidebar-section-title">RESOURCES</div>}

        <div className="sidebar-menu-item" onClick={openSettings}>
          <Settings size={15} />
          {!isCollapsed && <span>System Settings</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('education', 'Education Resources')}>
          <GraduationCap size={15} />
          {!isCollapsed && <span>Education</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('tradePlan', 'My Trade Plan')}>
          <FileSpreadsheet size={15} />
          {!isCollapsed && <span>Trade Plan</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('tradeLog', 'Trade Log')}>
          <History size={15} />
          {!isCollapsed && <span>Trade Log</span>}
        </div>
      </div>
    </aside>
  );
};
