/**
 * Manual command panel (FEAT-UI-31).
 *
 * Issues one bounded manual command at a time and renders the receipt the
 * server returned. Nothing is applied optimistically: no position appears, no
 * order disappears, and no fill is shown until the authoritative session state
 * that came back with the receipt says so.
 */

"use client";

import { useCallback, useState, type ReactNode } from "react";

import {
  ApiClientError,
  apiClients,
  type CommandReceipt,
  type CommandType,
  type LiveSessionCommandInput,
  type LiveSessionProjection,
} from "@/clients";

/** Commands offered by the panel, in the frozen contract order. */
export const MANUAL_COMMANDS: readonly (readonly [CommandType, string])[] = [
  ["submit_order", "Submit order"],
  ["modify_pending_order", "Modify pending order"],
  ["cancel_pending_order", "Cancel pending order"],
  ["close_position", "Close position"],
  ["reduce_position", "Reduce position"],
  ["close_all_practice_exposure", "Close all practice exposure"],
];

/** Resolve a failure message without implying the command succeeded. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The command could not be delivered.";
}

/** Props accepted by `ManualCommandPanel`. */
export interface ManualCommandPanelProps {
  sessionId: string;
  session: LiveSessionProjection | null;
  onSessionRefreshed?: (session: LiveSessionProjection) => void;
  className?: string;
}

/** Bounded manual trading controls for one practice session. */
export function ManualCommandPanel({
  sessionId,
  session,
  onSessionRefreshed,
  className = "",
}: ManualCommandPanelProps): ReactNode {
  const [command, setCommand] = useState<CommandType>("submit_order");
  const [symbol, setSymbol] = useState("");
  const [side, setSide] = useState<"buy" | "sell">("buy");
  const [orderType, setOrderType] = useState<"market" | "limit" | "stop">(
    "market",
  );
  const [volume, setVolume] = useState("0.10");
  const [price, setPrice] = useState("");
  const [stopLoss, setStopLoss] = useState("");
  const [takeProfit, setTakeProfit] = useState("");
  const [orderId, setOrderId] = useState("");
  const [positionId, setPositionId] = useState("");

  const [receipt, setReceipt] = useState<CommandReceipt | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const blocked =
    !session ||
    Boolean(session.exposure_blocked) ||
    Boolean((session as { finalized?: boolean }).finalized);

  const submit = useCallback(async () => {
    if (blocked || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const input: LiveSessionCommandInput = {
        command,
        ...(symbol.trim() ? { symbol: symbol.trim() } : {}),
        ...(command === "submit_order"
          ? { side, order_type: orderType, volume }
          : {}),
        ...(command === "close_position" || command === "reduce_position"
          ? { volume, position_id: positionId.trim() }
          : {}),
        ...(command === "cancel_pending_order" ||
        command === "modify_pending_order"
          ? { order_id: orderId.trim() }
          : {}),
        ...(price.trim() ? { price } : {}),
        ...(stopLoss.trim() ? { stop_loss: stopLoss } : {}),
        ...(takeProfit.trim() ? { take_profit: takeProfit } : {}),
      };
      const response = await apiClients.simulationWorkbench.submitCommand(
        sessionId,
        input,
      );
      if (response.status === "error") {
        setError(response.error.message);
        return;
      }
      setReceipt(response.data);
      const refreshed = await apiClients.simulationWorkbench.getLiveSession(
        sessionId,
      );
      if (refreshed.status === "success") {
        onSessionRefreshed?.(refreshed.data);
      }
    } catch (cause) {
      setError(failureMessage(cause));
    } finally {
      setSubmitting(false);
    }
  }, [
    blocked,
    submitting,
    command,
    symbol,
    side,
    orderType,
    volume,
    positionId,
    orderId,
    price,
    stopLoss,
    takeProfit,
    sessionId,
    onSessionRefreshed,
  ]);

  return (
    <section
      className={`simulation-command-panel ${className}`.trim()}
      aria-label="Manual command panel"
    >
      <h4>Manual command</h4>

      <label htmlFor="command-type">Command</label>
      <select
        id="command-type"
        value={command}
        onChange={(event) => setCommand(event.target.value as CommandType)}
      >
        {MANUAL_COMMANDS.map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>

      {command === "submit_order" ? (
        <>
          <label htmlFor="command-symbol">Symbol</label>
          <input
            id="command-symbol"
            value={symbol}
            onChange={(event) => setSymbol(event.target.value)}
          />
          <label htmlFor="command-side">Side</label>
          <select
            id="command-side"
            value={side}
            onChange={(event) =>
              setSide(event.target.value as "buy" | "sell")
            }
          >
            <option value="buy">Buy</option>
            <option value="sell">Sell</option>
          </select>
          <label htmlFor="command-order-type">Order type</label>
          <select
            id="command-order-type"
            value={orderType}
            onChange={(event) =>
              setOrderType(event.target.value as "market" | "limit" | "stop")
            }
          >
            <option value="market">Market</option>
            <option value="limit">Limit</option>
            <option value="stop">Stop</option>
          </select>
        </>
      ) : null}

      {command === "cancel_pending_order" ||
      command === "modify_pending_order" ? (
        <>
          <label htmlFor="command-order-id">Order ID</label>
          <input
            id="command-order-id"
            value={orderId}
            onChange={(event) => setOrderId(event.target.value)}
          />
        </>
      ) : null}

      {command === "close_position" || command === "reduce_position" ? (
        <>
          <label htmlFor="command-position-id">Position ID</label>
          <input
            id="command-position-id"
            value={positionId}
            onChange={(event) => setPositionId(event.target.value)}
          />
        </>
      ) : null}

      {command !== "close_all_practice_exposure" &&
      command !== "cancel_pending_order" ? (
        <>
          <label htmlFor="command-volume">Volume</label>
          <input
            id="command-volume"
            value={volume}
            onChange={(event) => setVolume(event.target.value)}
          />
        </>
      ) : null}

      {command !== "close_all_practice_exposure" ? (
        <>
          <label htmlFor="command-price">Price</label>
          <input
            id="command-price"
            value={price}
            onChange={(event) => setPrice(event.target.value)}
          />
          <label htmlFor="command-stop-loss">Stop loss</label>
          <input
            id="command-stop-loss"
            value={stopLoss}
            onChange={(event) => setStopLoss(event.target.value)}
          />
          <label htmlFor="command-take-profit">Take profit</label>
          <input
            id="command-take-profit"
            value={takeProfit}
            onChange={(event) => setTakeProfit(event.target.value)}
          />
        </>
      ) : null}

      <button type="button" onClick={() => void submit()} disabled={blocked || submitting}>
        {submitting ? "Sending…" : "Send command"}
      </button>

      {blocked ? (
        <p role="note">
          This session does not currently accept manual commands.
        </p>
      ) : null}

      {error ? <p role="alert">{error}</p> : null}

      {receipt ? (
        <dl className="simulation-command-panel__receipt" aria-label="Command receipt">
          <dt>Receipt</dt>
          <dd className="font-mono">{receipt.receipt_id}</dd>
          <dt>Command</dt>
          <dd>{receipt.command_type}</dd>
          <dt>Status</dt>
          <dd>{receipt.status}</dd>
          <dt>Reason</dt>
          <dd>{receipt.reason ?? "—"}</dd>
          <dt>Order</dt>
          <dd className="font-mono">{receipt.order_id ?? "—"}</dd>
          <dt>Position</dt>
          <dd className="font-mono">{receipt.position_id ?? "—"}</dd>
        </dl>
      ) : null}
    </section>
  );
}
