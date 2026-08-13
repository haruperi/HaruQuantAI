import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { CmeProgressBar } from './CmeProgressBar';

describe('CmeProgressBar', () => {
  afterEach(() => {
    cleanup();
  });

  it('renders percentage and status text for quantitative progress', () => {
    render(<CmeProgressBar value={2} max={4} label="Loading directory…" subtext="Page 2 of 4" />);
    expect(screen.getByText('Loading directory…')).toBeTruthy();
    expect(screen.getByText('Page 2 of 4 (50%)')).toBeTruthy();
    const bar = screen.getByRole('progressbar');
    expect(bar.getAttribute('aria-valuenow')).toBe('50');
  });

  it('handles 0% and 100% boundary conditions', () => {
    const { rerender } = render(<CmeProgressBar value={0} max={100} label="Start" />);
    expect(screen.getByText('0%')).toBeTruthy();

    rerender(<CmeProgressBar value={100} max={100} label="Done" />);
    expect(screen.getByText('100%')).toBeTruthy();
  });

  it('supports indeterminate loading state', () => {
    render(<CmeProgressBar value={0} max={100} label="Fetching stream…" indeterminate />);
    expect(screen.getByText('Fetching stream…')).toBeTruthy();
    const bar = screen.getByRole('progressbar');
    expect(bar.getAttribute('aria-valuenow')).toBeNull();
  });
});
