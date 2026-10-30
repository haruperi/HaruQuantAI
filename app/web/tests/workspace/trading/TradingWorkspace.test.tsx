import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { TradingDashboard } from '../../../workspaces/trading/TradingDashboard';
import { TradingWorkspace } from '../../../workspaces/trading/TradingWorkspace';

describe('TradingWorkspace Component (Phase LT.5)', () => {
  it('renders workspace layout and header', () => {
    const html = renderToString(<TradingWorkspace />);
    expect(html).toContain('Live Trading Operations');
    expect(html).toContain('Real-time broker telemetry, order routing, positions monitoring');
  });

  it('renders dashboard components including accounts, metrics, and tabs', () => {
    const html = renderToString(<TradingDashboard />);
    // Accounts and status
    expect(html).toContain('Active Connection');
    expect(html).toContain('MetaTrader 5');

    // Metrics cards
    expect(html).toContain('Balance');
    expect(html).toContain('Equity');
    expect(html).toContain('Used Margin');
    expect(html).toContain('Free Margin');
    expect(html).toContain('Margin Level');
    expect(html).toContain('Floating P/L');

    // Emergency and orders controls
    expect(html).toContain('Flatten All');
    expect(html).toContain('Cancel All Orders');
    expect(html).toContain('Emergency Kill Switch');
    expect(html).toContain('New Order');

    // Tabs
    expect(html).toContain('Open Positions');
    expect(html).toContain('Pending Orders');
    expect(html).toContain('Execution Journal');
  });
});
