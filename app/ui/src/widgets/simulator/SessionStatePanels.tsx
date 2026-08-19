/**
 * Authoritative session state panels (FEAT-UI-31).
 *
 * Renders the account, positions, and orders exactly as the session projection
 * reported them. These panels derive nothing: unrealised PnL, margin level,
 * and order status are server figures, and a field the server omitted is shown
 * as unavailable rather than computed locally.
 */

"use client";

import type { ReactNode } from "react";

import type { LiveSessionProjection } from "@/clients";

/** Render one owner value, or a dash when the server omitted it. */
function cell(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

/** Props accepted by `SessionStatePanels`. */
export interface SessionStatePanelsProps {
  session: LiveSessionProjection | null;
  className?: string;
}

/** Account strip, open positions, and resting orders for one session. */
export function SessionStatePanels({
  session,
  className = "",
}: SessionStatePanelsProps): ReactNode {
  if (!session) {
    return (
      <section
        className={`simulation-state-panels ${className}`.trim()}
        aria-label="Session state"
      >
        <p>No authoritative session state has been read yet.</p>
      </section>
    );
  }

  const account = session.account ?? null;

  return (
    <section
      className={`simulation-state-panels ${className}`.trim()}
      aria-label="Session state"
    >
      <section aria-label="Account">
        <h4>Account</h4>
        <dl className="simulation-state-panels__account">
          <dt>Currency</dt>
          <dd>{cell(account?.currency)}</dd>
          <dt>Balance</dt>
          <dd>{cell(account?.balance)}</dd>
          <dt>Equity</dt>
          <dd>{cell(account?.equity)}</dd>
          <dt>Margin</dt>
          <dd>{cell(account?.margin)}</dd>
          <dt>Free margin</dt>
          <dd>{cell(account?.free_margin)}</dd>
          <dt>Margin level</dt>
          <dd>{cell(account?.margin_level)}</dd>
        </dl>
      </section>

      <section aria-label="Positions">
        <h4>Positions</h4>
        {session.positions.length > 0 ? (
          <table>
            <caption className="sr-only">Open simulated positions</caption>
            <thead>
              <tr>
                <th scope="col">Position</th>
                <th scope="col">Symbol</th>
                <th scope="col">Side</th>
                <th scope="col">Volume</th>
                <th scope="col">Open price</th>
                <th scope="col">Stop loss</th>
                <th scope="col">Take profit</th>
                <th scope="col">Unrealized PnL</th>
              </tr>
            </thead>
            <tbody>
              {session.positions.map((position) => (
                <tr key={position.position_id}>
                  <td className="font-mono">{position.position_id}</td>
                  <td>{position.symbol}</td>
                  <td>{position.side}</td>
                  <td>{cell(position.volume)}</td>
                  <td>{cell(position.open_price)}</td>
                  <td>{cell(position.stop_loss)}</td>
                  <td>{cell(position.take_profit)}</td>
                  <td>{cell(position.unrealized_pnl)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No position is open.</p>
        )}
      </section>

      <section aria-label="Orders">
        <h4>Orders</h4>
        {session.orders.length > 0 ? (
          <table>
            <caption className="sr-only">Resting simulated orders</caption>
            <thead>
              <tr>
                <th scope="col">Order</th>
                <th scope="col">Symbol</th>
                <th scope="col">Type</th>
                <th scope="col">Side</th>
                <th scope="col">Volume</th>
                <th scope="col">Price</th>
                <th scope="col">Stop loss</th>
                <th scope="col">Take profit</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              {session.orders.map((order) => (
                <tr key={order.order_id}>
                  <td className="font-mono">{order.order_id}</td>
                  <td>{order.symbol}</td>
                  <td>{cell(order.order_type)}</td>
                  <td>{order.side}</td>
                  <td>{cell(order.volume)}</td>
                  <td>{cell(order.price)}</td>
                  <td>{cell(order.stop_loss)}</td>
                  <td>{cell(order.take_profit)}</td>
                  <td>{order.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No order is resting.</p>
        )}
      </section>

      <p className="simulation-state-panels__note">
        Pending intents awaiting the next tick: {session.pending_intent_count}
      </p>
    </section>
  );
}
