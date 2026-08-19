import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Sidebar, DOMAIN_GROUPS } from './Sidebar';

const mockAddWidgetToWorkspace = vi.fn();
const mockOpenSettings = vi.fn();

vi.mock('../../store/useTradingStore', () => ({
  useTradingStore: () => ({
    openSettings: mockOpenSettings,
  }),
}));

vi.mock('../../widgets/workspaces', () => ({
  useWorkspaceStore: () => ({
    addWidgetToWorkspace: mockAddWidgetToWorkspace,
  }),
}));

describe('Sidebar Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all 12 domain headers', () => {
    render(<Sidebar />);

    expect(DOMAIN_GROUPS).toHaveLength(12);
    DOMAIN_GROUPS.forEach((domain) => {
      expect(screen.getByTestId(`domain-header-${domain.id}`)).toBeInTheDocument();
      expect(screen.getByText(domain.label.toUpperCase())).toBeInTheDocument();
    });
  });

  it('toggles domain dropdown expansion on header click', () => {
    render(<Sidebar />);

    // By default, strategy is closed
    expect(screen.queryByTestId('widget-strategies')).not.toBeInTheDocument();

    // Click strategy header to open
    const strategyHeader = screen.getByTestId('domain-header-strategy');
    fireEvent.click(strategyHeader);

    // Now strategies widget item is visible
    expect(screen.getByTestId('widget-strategies')).toBeInTheDocument();

    // Click again to close
    fireEvent.click(strategyHeader);
    expect(screen.queryByTestId('widget-strategies')).not.toBeInTheDocument();
  });

  it('adds widget to workspace when widget item is clicked', () => {
    render(<Sidebar />);

    // Data is open by default -> click Markets widget
    const marketsItem = screen.getByTestId('widget-markets');
    fireEvent.click(marketsItem);

    expect(mockAddWidgetToWorkspace).toHaveBeenCalledWith('markets', 'Markets', undefined);

    // Indicators is open by default -> click Chart widget
    const chartItem = screen.getByTestId('widget-chart');
    fireEvent.click(chartItem);

    expect(mockAddWidgetToWorkspace).toHaveBeenCalledWith('chart', 'EURUSD Chart', 'EURUSD');
  });

  it('opens system settings modal when system settings is clicked', () => {
    render(<Sidebar />);

    // Open resources domain
    const resourcesHeader = screen.getByTestId('domain-header-resources');
    fireEvent.click(resourcesHeader);

    const settingsItem = screen.getByTestId('widget-settings');
    fireEvent.click(settingsItem);

    expect(mockOpenSettings).toHaveBeenCalledTimes(1);
  });

  it('collapses sidebar and renders domain icon buttons', () => {
    render(<Sidebar />);

    const toggleBtn = screen.getByTestId('sidebar-toggle-btn');
    expect(screen.getByText('HIDE MENU')).toBeInTheDocument();

    // Click toggle button to collapse
    fireEvent.click(toggleBtn);

    // In collapsed mode, "HIDE MENU" is gone
    expect(screen.queryByText('HIDE MENU')).not.toBeInTheDocument();

    // Domain icon buttons are present
    DOMAIN_GROUPS.forEach((domain) => {
      expect(screen.getByTestId(`domain-icon-${domain.id}`)).toBeInTheDocument();
    });
  });

  it('opens flyout menu in collapsed mode and adds widget from flyout', () => {
    render(<Sidebar />);

    // Collapse sidebar
    const toggleBtn = screen.getByTestId('sidebar-toggle-btn');
    fireEvent.click(toggleBtn);

    // Click on Data icon button
    const dataIcon = screen.getByTestId('domain-icon-data');
    fireEvent.click(dataIcon);

    // Flyout menu should be open
    expect(screen.getByTestId('flyout-data')).toBeInTheDocument();

    // Click Markets inside flyout
    const marketsFlyoutItem = screen.getByTestId('widget-markets');
    fireEvent.click(marketsFlyoutItem);

    expect(mockAddWidgetToWorkspace).toHaveBeenCalledWith('markets', 'Markets', undefined);

    // Flyout should close after selection
    expect(screen.queryByTestId('flyout-data')).not.toBeInTheDocument();
  });
});
