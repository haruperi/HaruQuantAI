import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MarketHoursWidget } from './MarketHoursWidget';

describe('MarketHoursWidget (FEAT-UI-30 / FR-UI-259 through FR-UI-264)', () => {
  it('FR-UI-259: renders widget container, header title, live sessions badge, and sandboxed iframe', () => {
    render(<MarketHoursWidget />);

    expect(screen.getByTestId('market-hours-widget')).toBeInTheDocument();
    expect(screen.getByText('FX Market Hours')).toBeInTheDocument();
    expect(screen.getByTestId('market-hours-live-badge')).toHaveTextContent('LIVE SESSIONS');

    const iframe = screen.getByTestId('market-hours-iframe') as HTMLIFrameElement;
    expect(iframe).toBeInTheDocument();
    expect(iframe.getAttribute('srcdoc')).toContain('type":"fxmarkethours"');
    expect(iframe.getAttribute('srcdoc')).toContain('freeserv-static.dukascopy.com/2.0/core.js');
    expect(iframe.getAttribute('srcdoc')).toContain('#0b0f19');
  });

  it('FR-UI-260: passes configured instrument and indicators to the Dukascopy applet params', () => {
    render(
      <MarketHoursWidget
        config={{
          instrument: 'GBP/USD',
          displaySpreadIndicator: true,
          displayVolatilityIndicator: true,
          displayVolumeIndicator: false,
        }}
      />
    );

    const iframe = screen.getByTestId('market-hours-iframe') as HTMLIFrameElement;
    const srcDoc = iframe.getAttribute('srcdoc') || '';
    expect(srcDoc).toContain('"instrument":"GBP/USD"');
    expect(srcDoc).toContain('"displaySpreadIndicator":true');
    expect(srcDoc).toContain('"displayVolatilityIndicator":true');
    expect(srcDoc).toContain('"displayVolumeIndicator":false');
  });

  it('FR-UI-261: configures timezone settings in applet params', () => {
    render(
      <MarketHoursWidget
        config={{
          defaultTimezone: 2,
          allowTimezoneChange: true,
        }}
      />
    );

    const iframe = screen.getByTestId('market-hours-iframe') as HTMLIFrameElement;
    const srcDoc = iframe.getAttribute('srcdoc') || '';
    expect(srcDoc).toContain('"defaultTimezone":2');
    expect(srcDoc).toContain('"allowTimezoneChange":true');
  });

  it('FR-UI-262: handles iframe loading overlay and transition upon load completion', () => {
    render(<MarketHoursWidget />);

    expect(screen.getByTestId('market-hours-loading')).toBeInTheDocument();
    expect(screen.getByText(/Connecting to Market Hours feed/i)).toBeInTheDocument();

    const iframe = screen.getByTestId('market-hours-iframe');
    act(() => {
      fireEvent.load(iframe);
    });

    expect(screen.queryByTestId('market-hours-loading')).not.toBeInTheDocument();
  });

  it('respects custom height, title, and className props', () => {
    render(
      <MarketHoursWidget
        height={650}
        title="Session Clocks"
        className="custom-market-hours-class"
      />
    );

    const widget = screen.getByTestId('market-hours-widget');
    expect(widget).toHaveClass('custom-market-hours-class');
    expect(widget).toHaveStyle({ height: '650px' });
    expect(screen.getByText('Session Clocks')).toBeInTheDocument();
  });
});
