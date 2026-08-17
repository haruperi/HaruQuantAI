import { fireEvent, render, screen } from '@testing-library/react';
import type { ComponentProps } from 'react';
import { describe, expect, it, vi } from 'vitest';

import { AccountMetricsMenu } from './AccountMetricsMenu';

const renderMenu = (
  overrides: Partial<ComponentProps<typeof AccountMetricsMenu>> = {},
) => render(
  <AccountMetricsMenu
    open
    accountMode="sim"
    leverage={null}
    profitDisplay="money"
    onProfitDisplayChange={vi.fn()}
    onClose={vi.fn()}
    {...overrides}
  />,
);

describe('AccountMetricsMenu', () => {
  it('explains provider-owned leverage outside SIM', () => {
    renderMenu({ accountMode: 'demo', leverage: 100 });
    expect(screen.getByRole('spinbutton', { name: 'Leverage' })).toHaveValue(100);
    expect(screen.getByText('Leverage is supplied automatically by MT5.')).toBeInTheDocument();
  });

  it('closes on Escape', () => {
    const onClose = vi.fn();
    renderMenu({ onClose });
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('closes after an outside pointer action', () => {
    const onClose = vi.fn();
    renderMenu({ onClose });
    fireEvent.mouseDown(document.body);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('offers Money and Percent as selectable profit displays', () => {
    const onProfitDisplayChange = vi.fn();
    renderMenu({ onProfitDisplayChange });
    expect(screen.getByRole('radio', { name: 'Money' })).toBeChecked();
    const percent = screen.getByRole('radio', { name: 'Percent' });
    expect(percent).toBeEnabled();
    fireEvent.click(percent);
    expect(onProfitDisplayChange).toHaveBeenCalledWith('percent');
  });
});
