import React, { useState } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
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
  HelpCircle,
  ThumbsUp,
  Info,
  ShieldAlert,
  Cookie
} from 'lucide-react';

export const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { addWidgetToWorkspace } = useTradingStore();

  const handleAddWidget = (type, title) => {
    addWidgetToWorkspace(type, title);
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

        <div className="sidebar-menu-item" onClick={() => handleAddWidget('chart', 'ESU6 Chart')}>
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

        <div className="sidebar-menu-item" onClick={() => alert('CME Group Simulator Help')}>
          <HelpCircle size={15} />
          {!isCollapsed && <span>Help</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => alert('Send Feedback')}>
          <ThumbsUp size={15} />
          {!isCollapsed && <span>Feedback</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => alert('About CME Trading Simulator')}>
          <Info size={15} />
          {!isCollapsed && <span>About</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => alert('Legal Terms & Conditions')}>
          <ShieldAlert size={15} />
          {!isCollapsed && <span>Legal</span>}
        </div>

        <div className="sidebar-menu-item" onClick={() => alert('Cookie Settings')}>
          <Cookie size={15} />
          {!isCollapsed && <span>Cookie Settings</span>}
        </div>
      </div>
    </aside>
  );
};
