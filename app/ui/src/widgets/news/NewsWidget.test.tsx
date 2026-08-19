import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { NewsWidget } from './NewsWidget';

describe('NewsWidget (FEAT-UI-29 / FR-UI-253 through FR-UI-258)', () => {
  it('FR-UI-253: renders widget container, header title, live badge, and sandboxed iframe without duplicate buttons', () => {
    render(<NewsWidget />);

    expect(screen.getByTestId('news-widget')).toBeInTheDocument();
    expect(screen.getByText('Online News')).toBeInTheDocument();
    expect(screen.getByText('Live')).toBeInTheDocument();

    // Verify duplicate toolbar buttons are not rendered in the host header
    expect(screen.queryByRole('button', { name: 'All' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Finance' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Forex' })).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Select news language')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Refresh news feed')).not.toBeInTheDocument();

    const iframe = screen.getByTestId('news-iframe') as HTMLIFrameElement;
    expect(iframe).toBeInTheDocument();
    expect(iframe.getAttribute('sandbox')).toContain('allow-scripts');
    expect(iframe.getAttribute('sandbox')).toContain('allow-popups');
    expect(iframe.getAttribute('srcdoc')).toContain('DukascopyApplet');
    expect(iframe.getAttribute('srcdoc')).toContain('online_news');
    expect(iframe.getAttribute('srcdoc')).toContain('freeserv-static.dukascopy.com');
  });

  it('FR-UI-254: passes configured categories to the Dukascopy applet params', () => {
    render(<NewsWidget defaultCategories={['finance', 'forex']} />);

    const iframe = screen.getByTestId('news-iframe') as HTMLIFrameElement;
    const srcDoc = iframe.getAttribute('srcdoc') || '';
    expect(srcDoc).toContain('"newsCategories":["finance","forex"]');
  });

  it('FR-UI-255: configures language settings in applet params and HTML lang attribute', () => {
    render(<NewsWidget defaultLanguage="es" />);

    const iframe = screen.getByTestId('news-iframe') as HTMLIFrameElement;
    const srcDoc = iframe.getAttribute('srcdoc') || '';
    expect(srcDoc).toContain('"defaultLanguage":"es"');
    expect(srcDoc).toContain('lang="es"');
  });

  it('FR-UI-256: handles iframe loading overlay and transition upon load completion', () => {
    render(<NewsWidget />);

    // Initially loading
    expect(screen.getByTestId('news-loading')).toBeInTheDocument();

    const iframe = screen.getByTestId('news-iframe');
    fireEvent.load(iframe);

    // After load, loading indicator is removed
    expect(screen.queryByTestId('news-loading')).not.toBeInTheDocument();
  });

  it('respects custom height and className props', () => {
    render(<NewsWidget className="custom-test-class" height={600} />);

    const widgetEl = screen.getByTestId('news-widget');
    expect(widgetEl.className).toContain('custom-test-class');
    expect(widgetEl.style.height).toBe('600px');
  });
});
