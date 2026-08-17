import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { PriceLadderWidget } from './PriceLadderWidget';

const {
  depthStreamMock,
  quotesMock,
  sessionMock,
  preflightOrderMock,
  submitOrderMock,
  preflightCancelAllOrdersMock,
  cancelAllOrdersMock,
  closePositionMock,
} = vi.hoisted(() => ({
  depthStreamMock: vi.fn(),
  quotesMock: vi.fn(),
  sessionMock: vi.fn(),
  preflightOrderMock: vi.fn(),
  submitOrderMock: vi.fn(),
  preflightCancelAllOrdersMock: vi.fn(),
  cancelAllOrdersMock: vi.fn(),
  closePositionMock: vi.fn(),
}));

let orderConfirmationRequired = false;
vi.mock('../workspaces', () => ({
  useWorkspaceStore: () => ({
    get orderConfirmationRequired() {
      return orderConfirmationRequired;
    },
  }),
}));

vi.mock('../../clients', () => ({
  apiClients: {
    data: { depthStream: depthStreamMock, quotes: quotesMock },
    trading: {
      session: sessionMock,
      preflightOrder: preflightOrderMock,
      submitOrder: submitOrderMock,
      preflightCancelAllOrders: preflightCancelAllOrdersMock,
      cancelAllOrders: cancelAllOrdersMock,
      preflightCancelOrder: vi.fn(),
      cancelOrder: vi.fn(),
      closePosition: closePositionMock,
    },
  },
  listWorkingOrders: (projection: { orders?: Record<string, unknown> }) =>
    Object.values(projection.orders ?? {}),
  listPositions: (projection: { positions?: Record<string, unknown> }) =>
    Object.values(projection.positions ?? {}),
}));

function emptyBookStream(): AsyncIterable<unknown> {
  return (async function* () {
    yield {
      sequence: 1,
      payload: {
        stale: false,
        gap: 0,
        source_id: 'mt5',
        books: [
          {
            symbol: 'EURUSD',
            book_depth: 1,
            bids: [{ price: '1.1000', volume: '50' }],
            asks: [{ price: '1.1002', volume: '40' }],
          },
        ],
        errors: [],
      },
    };
    await new Promise(() => {});
  })();
}

describe('PriceLadderWidget — FR-UI-055 through FR-UI-062', () => {
  beforeEach(() => {
    orderConfirmationRequired = false;
    depthStreamMock.mockReset();
    sessionMock.mockReset();
    preflightOrderMock.mockReset();
    submitOrderMock.mockReset();
    preflightCancelAllOrdersMock.mockReset();
    cancelAllOrdersMock.mockReset();
    quotesMock.mockReset();
    closePositionMock.mockReset();
    depthStreamMock.mockImplementation(() => emptyBookStream());
    sessionMock.mockResolvedValue({ status: 'success', data: { orders: {} } });
    quotesMock.mockResolvedValue({ status: 'success', data: { rows: [] } });
  });

  afterEach(() => {
    cleanup();
  });

  it('renders real bid/ask levels from the depth feed (FR-UI-055/056)', async () => {
    render(<PriceLadderWidget symbol="EURUSD" accountId="acct-1" />);

    await waitFor(() => expect(screen.getByText('50')).toBeTruthy());
    expect(screen.getByText('40')).toBeTruthy();
    expect(screen.getAllByText('1.10000').length).toBeGreaterThan(0);
  });

  it('never submits when the real Risk preflight declines (FR-UI-055 fail-closed)', async () => {
    preflightOrderMock.mockResolvedValue({
      status: 'success',
      data: {
        state: 'needs_more_evidence',
        risk_decision_id: 'decision-1',
        action_policy_verdict_id: null,
        approval_token_ref: null,
        reasons: ['historical_var'],
        expires_at: '2026-01-01T00:00:00Z',
      },
    });

    render(<PriceLadderWidget symbol="EURUSD" accountId="acct-1" />);
    await waitFor(() => expect(screen.getByText('50')).toBeTruthy());

    fireEvent.click(screen.getByText(/BUY MKT/));

    await waitFor(() => expect(preflightOrderMock).toHaveBeenCalledTimes(1));
    expect(submitOrderMock).not.toHaveBeenCalled();
    await waitFor(() =>
      expect(screen.getByText(/not approved: needs_more_evidence/)).toBeTruthy()
    );
  });

  it('submits with the real preflight governance ids once approved (FR-UI-058)', async () => {
    preflightOrderMock.mockResolvedValue({
      status: 'success',
      data: {
        state: 'approve',
        risk_decision_id: 'decision-1',
        action_policy_verdict_id: 'verdict-1',
        approval_token_ref: 'token-1',
        reasons: [],
        expires_at: '2026-01-01T00:00:00Z',
      },
    });
    submitOrderMock.mockResolvedValue({ status: 'success', data: {} });

    render(<PriceLadderWidget symbol="EURUSD" accountId="acct-1" />);
    await waitFor(() => expect(screen.getByText('50')).toBeTruthy());

    fireEvent.click(screen.getByText(/BUY MKT/));

    await waitFor(() => expect(submitOrderMock).toHaveBeenCalledTimes(1));
    const submitted = submitOrderMock.mock.calls[0][0];
    expect(submitted.risk_decision_id).toBe('decision-1');
    expect(submitted.action_policy_verdict_id).toBe('verdict-1');
    expect(submitted.approval_token_ref).toBe('token-1');
    expect(submitted.strategy_id).toBe('discretionary-manual-order');
  });

  it('requires explicit confirmation before cancel-all executes, regardless of the workspace setting (FR-UI-061)', async () => {
    orderConfirmationRequired = false;
    sessionMock.mockResolvedValue({
      status: 'success',
      data: {
        orders: {
          'evt-1': {
            request_id: 'req-1',
            intent: {
              client_order_id: 'c-1',
              symbol: 'EURUSD',
              side: 'BUY',
              order_type: 'LIMIT',
              approved_volume: '1',
              price: '1.1000',
            },
            broker_order_id: 'broker-1',
          },
        },
      },
    });

    render(<PriceLadderWidget symbol="EURUSD" accountId="acct-1" />);
    await waitFor(() =>
      expect(
        (screen.getByTitle('Cancel All Working Orders') as HTMLButtonElement).disabled
      ).toBe(false)
    );

    fireEvent.click(screen.getByTitle('Cancel All Working Orders'));

    expect(cancelAllOrdersMock).not.toHaveBeenCalled();
    expect(preflightCancelAllOrdersMock).not.toHaveBeenCalled();
    expect(screen.getByText(/Cancel all 1 working EURUSD order/)).toBeTruthy();

    preflightCancelAllOrdersMock.mockResolvedValue({
      status: 'success',
      data: {
        state: 'approve',
        risk_decision_id: 'decision-2',
        action_policy_verdict_id: 'verdict-2',
        approval_token_ref: 'token-2',
        reasons: [],
        expires_at: '2026-01-01T00:00:00Z',
      },
    });
    cancelAllOrdersMock.mockResolvedValue({ status: 'success', data: {} });

    fireEvent.click(screen.getByText('Confirm Cancel All'));

    await waitFor(() => expect(cancelAllOrdersMock).toHaveBeenCalledTimes(1));
  });

  it('renders real depth without an account, but disables trading actions (FR-UI-055 without FR-UI-058 authority)', async () => {
    render(<PriceLadderWidget symbol="EURUSD" />);

    await waitFor(() => expect(screen.getByText('50')).toBeTruthy());
    expect(screen.getByText(/NO ACCOUNT/)).toBeTruthy();
    expect((screen.getByText(/BUY MKT/) as HTMLButtonElement).disabled).toBe(true);
    expect(sessionMock).not.toHaveBeenCalled();
  });

  it('flattens only through an approved Risk review of the opposing order', async () => {
    sessionMock.mockResolvedValue({
      status: 'success',
      data: {
        orders: {},
        positions: {
          'pos-1': {
            position_id: 'pos-1',
            account_id: 'acct-1',
            symbol: 'EURUSD',
            broker_position_id: 'broker-pos-1',
            side: 'LONG',
            state: 'OPEN',
            quantity: '2',
          },
        },
      },
    });
    preflightOrderMock.mockResolvedValue({
      status: 'success',
      data: {
        state: 'approve',
        risk_decision_id: 'decision-3',
        action_policy_verdict_id: 'verdict-3',
        approval_token_ref: 'token-3',
        reasons: [],
        expires_at: '2026-01-01T00:00:00Z',
      },
    });
    closePositionMock.mockResolvedValue({ status: 'success', data: {} });

    render(<PriceLadderWidget symbol="EURUSD" accountId="acct-1" />);
    await waitFor(() =>
      expect((screen.getByText('FLATTEN') as HTMLButtonElement).disabled).toBe(false)
    );

    fireEvent.click(screen.getByText('FLATTEN'));

    // Confirmation is mandatory, exactly as cancel-all is.
    expect(closePositionMock).not.toHaveBeenCalled();
    expect(screen.getByText(/Flatten 1 open EURUSD position/)).toBeTruthy();

    fireEvent.click(screen.getByText('Confirm Flatten'));

    await waitFor(() => expect(closePositionMock).toHaveBeenCalledTimes(1));
    // A long is unwound by a reviewed SELL of the same size.
    expect(preflightOrderMock.mock.calls[0][0].side).toBe('SELL');
    expect(preflightOrderMock.mock.calls[0][0].quantity).toBe(2);
    const [positionId, body] = closePositionMock.mock.calls[0];
    expect(positionId).toBe('broker-pos-1');
    expect(body.action).toBe('close_position');
    expect(body.target_broker_position_id).toBe('broker-pos-1');
    expect(body.risk_decision_id).toBe('decision-3');
    expect(body.approval_token_ref).toBe('token-3');
  });

  it('never flattens when the Risk review of the opposing order declines', async () => {
    sessionMock.mockResolvedValue({
      status: 'success',
      data: {
        orders: {},
        positions: {
          'pos-1': {
            position_id: 'pos-1',
            account_id: 'acct-1',
            symbol: 'EURUSD',
            broker_position_id: 'broker-pos-1',
            side: 'SHORT',
            state: 'OPEN',
            quantity: '1',
          },
        },
      },
    });
    preflightOrderMock.mockResolvedValue({
      status: 'success',
      data: {
        state: 'reject',
        risk_decision_id: 'decision-4',
        action_policy_verdict_id: null,
        approval_token_ref: null,
        reasons: ['exposure_limit'],
        expires_at: '2026-01-01T00:00:00Z',
      },
    });

    render(<PriceLadderWidget symbol="EURUSD" accountId="acct-1" />);
    await waitFor(() =>
      expect((screen.getByText('FLATTEN') as HTMLButtonElement).disabled).toBe(false)
    );

    fireEvent.click(screen.getByText('FLATTEN'));
    fireEvent.click(screen.getByText('Confirm Flatten'));

    await waitFor(() => expect(preflightOrderMock).toHaveBeenCalledTimes(1));
    expect(closePositionMock).not.toHaveBeenCalled();
    // A short is unwound by a BUY, and the rejection is surfaced verbatim.
    expect(preflightOrderMock.mock.calls[0][0].side).toBe('BUY');
    await waitFor(() =>
      expect(screen.getByText(/Flatten not approved: reject/)).toBeTruthy()
    );
  });

  it('re-centers on Spacebar as well as the pointer button (FR-UI-062)', async () => {
    const scrollIntoView = vi.fn();
    HTMLElement.prototype.scrollIntoView = scrollIntoView;

    render(<PriceLadderWidget symbol="EURUSD" accountId="acct-1" />);
    await waitFor(() => expect(screen.getByText('50')).toBeTruthy());

    fireEvent.click(screen.getByTitle(/Re-Center Price Ladder/));
    expect(scrollIntoView).toHaveBeenCalledTimes(1);

    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { code: 'Space' }));
    });
    expect(scrollIntoView).toHaveBeenCalledTimes(2);
  });
});
