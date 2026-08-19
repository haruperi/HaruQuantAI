"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ApiClientError, apiClients, type TradingAccountProfile, type TradingInstrumentConstraints } from "@/clients";
import { buildGovernedOptions } from "@/context";
import { filterSymbols, loadSymbolUniverse, resolveSourceSymbol } from "@/widgets/watchlists/symbolUniverse";
import { useWorkspaceStore } from "@/widgets/workspaces";
import { useTradingStore } from "@/store/useTradingStore";

type OrderType = "MARKET" | "LIMIT" | "STOP" | "STOP_LIMIT";
type Side = "BUY" | "SELL";
type ProtectionKind = "STOP_LOSS" | "TAKE_PROFIT";
type ProtectionField = "pips" | "price" | "balance" | "profit";
interface ProtectionValues { pips: string; price: string; balance: string; profit: string }
interface StrategyChoice { key: string; id: string; version: string; label: string }
export interface OrderTicketProps {
  readonly accountId?: string;
  readonly embedded?: boolean;
  readonly symbol?: string;
  readonly onSymbolChange?: (symbol: string) => void;
}

function id(prefix: string): string { return `${prefix}-${globalThis.crypto?.randomUUID?.() ?? Date.now().toString(36)}`; }
function isStepAligned(value: number, minimum: number, step: number): boolean { const quotient = (value - minimum) / step; return Math.abs(quotient - Math.round(quotient)) < 1e-8; }
const emptyProtection = (): ProtectionValues => ({ pips: "", price: "", balance: "", profit: "" });
function decimal(value: string | number | null | undefined): number | null { if (value === null || value === undefined || value === "") return null; const parsed = Number(value); return Number.isFinite(parsed) ? parsed : null; }
function fixed(value: number, digits: number): string { const rendered = value.toFixed(digits); return digits > 0 ? rendered.replace(/\.?0+$/u, "") : rendered; }
function calculateProtection(field: ProtectionField, raw: string, kind: ProtectionKind, side: Side, entry: number, quantity: number, balance: number, constraints: TradingInstrumentConstraints): ProtectionValues | null {
  const pipSize = decimal(constraints.pip_size); const tickSize = decimal(constraints.trade_tick_size); const tickValue = decimal(kind === "STOP_LOSS" ? constraints.trade_tick_value_loss : constraints.trade_tick_value_profit); const digits = constraints.digits;
  if (!(pipSize && tickSize && tickValue && quantity > 0 && digits !== null)) return null;
  const input = Number(raw); if (!Number.isFinite(input)) return null;
  const direction = kind === "STOP_LOSS" ? (side === "BUY" ? -1 : 1) : (side === "BUY" ? 1 : -1);
  let price: number; let profit: number;
  if (field === "pips") price = entry + direction * Math.abs(input) * pipSize;
  else if (field === "price") price = input;
  else {
    profit = field === "balance" ? input - balance : input;
    const expectedSign = kind === "STOP_LOSS" ? -1 : 1;
    if (profit === 0 || Math.sign(profit) !== expectedSign) return null;
    const ticks = Math.abs(profit) / (tickValue * quantity);
    price = entry + direction * ticks * tickSize;
  }
  const directedDistance = (price - entry) / direction;
  if (!(price > 0) || !(directedDistance > 0)) return null;
  const pips = directedDistance / pipSize;
  const ticks = directedDistance / tickSize;
  profit = (kind === "STOP_LOSS" ? -1 : 1) * ticks * tickValue * quantity;
  return { pips: fixed(pips, 2), price: fixed(price, digits), balance: fixed(balance + profit, 2), profit: fixed(profit, 2) };
}
function strategyChoices(rows: readonly Record<string, unknown>[]): StrategyChoice[] {
  const choices = new Map<string, StrategyChoice>();
  for (const row of rows) {
    const manifest = row.manifest && typeof row.manifest === "object" ? row.manifest as Record<string, unknown> : null;
    const strategyId = typeof manifest?.strategy_id === "string" ? manifest.strategy_id.trim() : "";
    const version = typeof manifest?.strategy_version === "string" ? manifest.strategy_version.trim() : "";
    const key = `${strategyId}@${version}`;
    if (!strategyId || !version || choices.has(key)) continue;
    choices.set(key, { key, id: strategyId, version, label: `${strategyId} · ${version}` });
  }
  return [...choices.values()].sort((left, right) => left.id.localeCompare(right.id) || left.version.localeCompare(right.version));
}

/** Private, fail-closed CFD/forex order ticket. */
export function OrderTicket({ accountId, embedded = false, symbol: configuredSymbol, onSymbolChange }: OrderTicketProps): React.JSX.Element | null {
  const { isOrderTicketOpen, orderTicketProps, closeOrderTicket } = useTradingStore();
  const { accountMode, orderConfirmationRequired, tradingModeCompatible } = useWorkspaceStore();
  const open = embedded || isOrderTicketOpen;
  const [symbolText, setSymbolText] = useState(configuredSymbol ?? orderTicketProps.symbol ?? "");
  const [symbolUniverse, setSymbolUniverse] = useState<string[]>([]);
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);
  const [activeSuggestionIndex, setActiveSuggestionIndex] = useState(-1);
  const suggestionIdPrefix = useRef(id("trading-symbol-suggestion"));
  const [strategies, setStrategies] = useState<StrategyChoice[]>([]);
  const [strategyKey, setStrategyKey] = useState("");
  const [side, setSide] = useState<Side | null>(null);
  const [orderType, setOrderType] = useState<OrderType>("MARKET");
  const [quantity, setQuantity] = useState("");
  const [limitPrice, setLimitPrice] = useState(""); const [stopPrice, setStopPrice] = useState("");
  const [stopLoss, setStopLoss] = useState(""); const [takeProfit, setTakeProfit] = useState("");
  const [stopLossValues, setStopLossValues] = useState<ProtectionValues>(emptyProtection);
  const [takeProfitValues, setTakeProfitValues] = useState<ProtectionValues>(emptyProtection);
  const [stopLossEnabled, setStopLossEnabled] = useState(false);
  const [takeProfitEnabled, setTakeProfitEnabled] = useState(false);
  const [timeInForce, setTimeInForce] = useState("");
  const [constraints, setConstraints] = useState<TradingInstrumentConstraints | null>(null);
  const [accountProfile, setAccountProfile] = useState<TradingAccountProfile | null>(null);
  const [quote, setQuote] = useState<{ bid: number | null; ask: number | null; generatedAt: string } | null>(null);
  const [symbolUniverseError, setSymbolUniverseError] = useState<string | null>(null);
  const [strategyError, setStrategyError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false); const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null); const [confirming, setConfirming] = useState(false);
  const symbol = useMemo(() => resolveSourceSymbol(symbolUniverse, symbolText), [symbolText, symbolUniverse]);
  const suggestions = useMemo(() => suggestionsOpen ? filterSymbols(symbolUniverse, symbolText, 12) : [], [suggestionsOpen, symbolText, symbolUniverse]);
  const strategy = strategies.find((choice) => choice.key === strategyKey) ?? null;
  const accountBalance = decimal(accountProfile?.balance);
  const marketEntry = side === "BUY" ? quote?.ask : side === "SELL" ? quote?.bid : null;
  // Pending protections are measured from the intended execution price; a
  // stop-limit's stop price is its trigger, while its limit price is its fill target.
  const calculatorEntry = orderType === "MARKET" ? marketEntry : orderType === "STOP" ? decimal(stopPrice) : decimal(limitPrice);
  const calculatorReady = Boolean(constraints && accountBalance !== null && accountProfile?.mode_compatible && accountProfile.currency && calculatorEntry !== null && calculatorEntry !== undefined && Number(quantity) > 0 && constraints.digits !== null && decimal(constraints.pip_size) && decimal(constraints.trade_tick_size) && decimal(constraints.trade_tick_value_profit) && decimal(constraints.trade_tick_value_loss) && decimal(constraints.trade_contract_size));

  function updateProtection(kind: ProtectionKind, field: ProtectionField, raw: string): void {
    const setter = kind === "STOP_LOSS" ? setStopLossValues : setTakeProfitValues;
    if (!raw) { setter(emptyProtection()); if (kind === "STOP_LOSS") setStopLoss(""); else setTakeProfit(""); return; }
    const calculated = constraints && side && calculatorEntry !== null && calculatorEntry !== undefined && accountBalance !== null ? calculateProtection(field, raw, kind, side, calculatorEntry, Number(quantity), accountBalance, constraints) : null;
    const values = calculated ?? { ...emptyProtection(), [field]: raw };
    setter(values);
    if (kind === "STOP_LOSS") setStopLoss(calculated?.price ?? ""); else setTakeProfit(calculated?.price ?? "");
  }

  function closeSuggestions(): void {
    setSuggestionsOpen(false);
    setActiveSuggestionIndex(-1);
  }

  function selectSymbol(candidate: string): void {
    const resolved = resolveSourceSymbol(symbolUniverse, candidate);
    if (resolved) setSymbolText(resolved);
    closeSuggestions();
  }

  function handleSymbolKeyDown(event: React.KeyboardEvent<HTMLInputElement>): void {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setSuggestionsOpen(true);
      setActiveSuggestionIndex((current) => suggestions.length === 0 ? -1 : (current + 1) % suggestions.length);
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setSuggestionsOpen(true);
      setActiveSuggestionIndex((current) => suggestions.length === 0 ? -1 : current <= 0 ? suggestions.length - 1 : current - 1);
      return;
    }
    if (event.key === "Escape") {
      closeSuggestions();
      return;
    }
    if ((event.key === "Enter" || event.key === "Tab") && suggestions.length > 0) {
      event.preventDefault();
      selectSymbol(suggestions[activeSuggestionIndex] ?? suggestions[0]);
    }
  }

  useEffect(() => {
    if (symbol) onSymbolChange?.(symbol);
  }, [onSymbolChange, symbol]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setSymbolUniverseError(null);
    void loadSymbolUniverse().then((universe) => {
      if (!cancelled) setSymbolUniverse(universe);
    }).catch((cause: unknown) => {
      if (!cancelled) setSymbolUniverseError(cause instanceof Error ? cause.message : "Symbol universe unavailable.");
    });
    return () => { cancelled = true; };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    void apiClients.trading.accountProfile().then((response) => {
      if (!cancelled) setAccountProfile(response.status === "success" ? response.data : null);
    }).catch(() => { if (!cancelled) setAccountProfile(null); });
    return () => { cancelled = true; };
  }, [open, accountMode]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setStrategyError(null);
    void apiClients.strategies.catalogue().then((response) => {
      if (cancelled) return;
      if (response.status === "error") throw new Error(response.error.message);
      const choices = strategyChoices(response.data); setStrategies(choices); setStrategyKey((current) => choices.some((choice) => choice.key === current) ? current : "");
    }).catch((cause: unknown) => {
      if (!cancelled) setStrategyError(cause instanceof Error ? cause.message : "Strategy catalogue unavailable.");
    });
    return () => { cancelled = true; };
  }, [open]);

  useEffect(() => {
    if (!open || !symbol) { setConstraints(null); setQuote(null); return; }
    let cancelled = false; setLoading(true); setError(null);
    void Promise.all([apiClients.trading.instrumentConstraints(symbol), apiClients.data.quotes([symbol])]).then(([constraintResponse, quoteResponse]) => {
      if (cancelled) return; if (constraintResponse.status === "error") throw new Error(constraintResponse.error.message); if (quoteResponse.status === "error") throw new Error(quoteResponse.error.message);
      const row = quoteResponse.data.rows[0]; setConstraints(constraintResponse.data); setQuote(row ? { bid: row.bid, ask: row.ask, generatedAt: quoteResponse.data.generated_at } : null); if (!row) setError("Current market evidence is unavailable.");
    }).catch((cause: unknown) => { if (!cancelled) setError(cause instanceof Error ? cause.message : "Order evidence unavailable."); }).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [open, symbol]);

  useEffect(() => { if (constraints && !constraints.supported_order_types.includes(orderType)) setOrderType(constraints.supported_order_types[0] ?? "MARKET"); }, [constraints, orderType]);
  useEffect(() => {
    if (stopLossEnabled && stopLossValues.price) updateProtection("STOP_LOSS", "price", stopLossValues.price);
    if (takeProfitEnabled && takeProfitValues.price) updateProtection("TAKE_PROFIT", "price", takeProfitValues.price);
  // Recalculate monetary estimates when the order context changes.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quantity, side, constraints, calculatorEntry, accountBalance]);
  const validation = useMemo(() => {
    if (!accountId) return "A verified Trading account is required."; if (!tradingModeCompatible || accountMode === "unknown") return "Selected and provider account modes must match.";
    if (!symbol) return "Choose an exact provider symbol."; if (!strategy) return "Choose a registered strategy."; if (!constraints || !quote) return "Authoritative instrument and market evidence is required."; if (!side) return "Choose BUY or SELL.";
    const numeric = Number(quantity); const minimum = Number(constraints.min_quantity); const maximum = Number(constraints.max_quantity); const step = Number(constraints.quantity_step);
    if (!Number.isFinite(numeric) || numeric <= 0) return "Enter a positive quantity."; if (numeric < minimum || numeric > maximum || !isStepAligned(numeric, minimum, step)) return `Quantity must be ${minimum}–${maximum} ${constraints.quantity_unit} in steps of ${step}.`;
    if ((orderType === "LIMIT" || orderType === "STOP_LIMIT") && !(Number(limitPrice) > 0)) return "A positive limit price is required."; if ((orderType === "STOP" || orderType === "STOP_LIMIT") && !(Number(stopPrice) > 0)) return "A positive stop price is required.";
    if (timeInForce && !constraints.supported_time_in_force.includes(timeInForce as never)) return "Unsupported time in force."; return null;
  }, [accountId, accountMode, constraints, limitPrice, orderType, quantity, quote, side, stopPrice, strategy, symbol, timeInForce, tradingModeCompatible]);

  async function submit(): Promise<void> {
    if (validation || !constraints || !quote || !side || !accountId || accountMode === "unknown" || !symbol || !strategy) return;
    setError(null); setResult(null); const workflow = id("wf"); const correlation = id("cor"); const idempotencyKey = id("idem"); const currentPrice = side === "BUY" ? quote.ask : quote.bid;
    if (currentPrice === null) { setError("The selected side has no current market price."); return; }
    try {
      const preflight = await apiClients.trading.preflightOrder({ request_id: id("req"), workflow_id: workflow, correlation_id: correlation, route: accountMode, account_id: accountId, symbol, side, order_type: orderType, quantity, current_price: currentPrice, idempotency_key: idempotencyKey }, { idempotencyKey });
      if (preflight.status === "error") { setError(preflight.error.message); return; } if (preflight.data.state !== "APPROVED" || !preflight.data.action_policy_verdict_id || !preflight.data.approval_token_ref) { setError(preflight.data.reasons.join("; ") || "Risk declined the order."); return; }
      const governed = buildGovernedOptions({ workflow, permission: "trading:write", actorId: "operator", evidenceId: preflight.data.risk_decision_id, idempotencyKey, routeId: accountMode }); const now = new Date();
      const submitted = await apiClients.trading.submitOrder({ request_id: id("req"), workflow_id: workflow, correlation_id: correlation, route: accountMode, action: "submit_order", account_id: accountId, strategy_id: strategy.id, strategy_version: strategy.version, intent_id: id("intent"), symbol, side, order_type: orderType, quantity_unit: constraints.quantity_unit, quantity, price: limitPrice || null, stop_price: stopPrice || null, stop_loss: constraints.supports_stop_loss && stopLossEnabled && stopLoss ? stopLoss : null, take_profit: constraints.supports_take_profit && takeProfitEnabled && takeProfit ? takeProfit : null, time_in_force: timeInForce ? timeInForce as "IOC" | "FOK" : null, risk_decision_id: preflight.data.risk_decision_id, action_policy_verdict_id: preflight.data.action_policy_verdict_id, approval_token_ref: preflight.data.approval_token_ref, idempotency_key: idempotencyKey, canonical_material_version: "v1", system_time: now.toISOString(), valid_until: preflight.data.expires_at }, governed.options);
      if (submitted.status === "error") { setError(submitted.error.message); return; } setResult("Order accepted by the Trading authority."); setConfirming(false);
    } catch (cause) { setError(cause instanceof ApiClientError ? `${cause.message}${cause.retryable ? " (retryable after reconciliation)" : ""}` : "Order outcome is unknown; reconcile before retrying."); }
  }

  if (!open) return null; const supportedTypes = constraints?.supported_order_types ?? ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"];
  const content = <section className="order-ticket" aria-label="Order ticket"><nav className="order-ticket__types" aria-label="Order types">{supportedTypes.map((value) => <button key={value} type="button" aria-pressed={orderType === value} onClick={() => setOrderType(value)}>{value.replace("_", "-").toLowerCase()} order</button>)}</nav><div className="order-ticket__body">
    <header><h3>New {orderType.replace("_", "-").toLowerCase()} order</h3><span>{accountMode.toUpperCase()}</span></header>
    <div className="order-ticket__selectors"><label className="order-ticket__symbol"><span>Symbol</span><div className="order-ticket__symbol-search"><input type="text" role="combobox" aria-label="Symbol" aria-expanded={suggestions.length > 0} aria-controls={`${suggestionIdPrefix.current}-listbox`} aria-autocomplete="list" aria-activedescendant={activeSuggestionIndex >= 0 ? `${suggestionIdPrefix.current}-${activeSuggestionIndex}` : undefined} autoComplete="off" value={symbolText} onChange={(event) => { setSymbolText(event.target.value); setSuggestionsOpen(true); setActiveSuggestionIndex(-1); }} onFocus={() => setSuggestionsOpen(true)} onBlur={() => window.setTimeout(closeSuggestions, 150)} onKeyDown={handleSymbolKeyDown} />{suggestions.length > 0 && <ul id={`${suggestionIdPrefix.current}-listbox`} role="listbox" aria-label="Symbol suggestions" className="order-ticket__symbol-suggestions">{suggestions.map((value, index) => <li key={value} id={`${suggestionIdPrefix.current}-${index}`} role="option" aria-selected={index === activeSuggestionIndex} onMouseDown={(event) => { event.preventDefault(); selectSymbol(value); }} onMouseEnter={() => setActiveSuggestionIndex(index)}>{value}</li>)}</ul>}</div></label><label><span>Strategy</span><select aria-label="Strategy" value={strategyKey} onChange={(event) => setStrategyKey(event.target.value)}><option value="">Select registered strategy</option>{strategies.map((choice) => <option key={choice.key} value={choice.key}>{choice.label}</option>)}</select></label></div>
    <div className="order-ticket__quotes" aria-label="Trade side"><button className="order-ticket__sell" type="button" aria-pressed={side === "SELL"} onClick={() => setSide("SELL")}><span>Sell</span><strong>{quote?.bid ?? "—"}</strong></button><button className="order-ticket__buy" type="button" aria-pressed={side === "BUY"} onClick={() => setSide("BUY")}><span>Buy</span><strong>{quote?.ask ?? "—"}</strong></button></div>{quote && <small className="order-ticket__freshness">Quote observed {quote.generatedAt}</small>}
    <div className="order-ticket__market-details">
      {orderType === "MARKET" ? <div className="order-ticket__market-top">
        <label><span>Quantity</span><span className="order-ticket__input-unit"><input aria-label="Ticket quantity" inputMode="decimal" value={quantity} onChange={(event) => setQuantity(event.target.value)} /><span>{constraints?.quantity_unit ?? "—"}</span></span><small>Est. margin: —</small></label>
        <div className="order-ticket__unsupported-control"><label className="order-ticket__check"><input type="checkbox" aria-label="Enable market range" disabled /><span>Market range</span></label><span className="order-ticket__input-unit"><input aria-label="Market range value" value="—" disabled /><span>Pips</span></span><small>Pip value: —</small></div>
      </div> : <div className="order-ticket__pending-top">
        {(orderType === "LIMIT" || orderType === "STOP_LIMIT") && <label><span>Limit price</span><input aria-label="Limit price" inputMode="decimal" value={limitPrice} onChange={(event) => setLimitPrice(event.target.value)} /></label>}
        {(orderType === "STOP" || orderType === "STOP_LIMIT") && <label><span>Stop price</span><input aria-label="Stop price" inputMode="decimal" value={stopPrice} onChange={(event) => setStopPrice(event.target.value)} /></label>}
        <label><span>Quantity</span><span className="order-ticket__input-unit"><input aria-label="Ticket quantity" inputMode="decimal" value={quantity} onChange={(event) => setQuantity(event.target.value)} /><span>{constraints?.quantity_unit ?? "—"}</span></span><small>Est. margin: —</small></label>
      </div>}
      <div className="order-ticket__protections" aria-label="Protection controls">
        <label className="order-ticket__check"><input type="checkbox" aria-label="Enable stop loss" checked={stopLossEnabled} disabled={!constraints?.supports_stop_loss || !calculatorReady} onChange={(event) => { setStopLossEnabled(event.target.checked); if (!event.target.checked) updateProtection("STOP_LOSS", "price", ""); }} /><span>Stop loss</span></label><span aria-hidden="true" /><label className="order-ticket__check"><input type="checkbox" aria-label="Enable take profit" checked={takeProfitEnabled} disabled={!constraints?.supports_take_profit || !calculatorReady} onChange={(event) => { setTakeProfitEnabled(event.target.checked); if (!event.target.checked) updateProtection("TAKE_PROFIT", "price", ""); }} /><span>Take profit 1</span></label>
        <input aria-label="Stop loss pips" inputMode="decimal" value={stopLossValues.pips} disabled={!stopLossEnabled || !calculatorReady} onChange={(event) => updateProtection("STOP_LOSS", "pips", event.target.value)} /><span className="order-ticket__protection-label">Pips</span><input aria-label="Take profit pips" inputMode="decimal" value={takeProfitValues.pips} disabled={!takeProfitEnabled || !calculatorReady} onChange={(event) => updateProtection("TAKE_PROFIT", "pips", event.target.value)} />
        <input aria-label="Stop loss price" inputMode="decimal" value={stopLossValues.price} disabled={!stopLossEnabled || !calculatorReady} onChange={(event) => updateProtection("STOP_LOSS", "price", event.target.value)} /><span className="order-ticket__protection-label">Price</span><input aria-label="Take profit price" inputMode="decimal" value={takeProfitValues.price} disabled={!takeProfitEnabled || !calculatorReady} onChange={(event) => updateProtection("TAKE_PROFIT", "price", event.target.value)} />
        <input aria-label="Stop loss balance" inputMode="decimal" value={stopLossValues.balance} disabled={!stopLossEnabled || !calculatorReady} onChange={(event) => updateProtection("STOP_LOSS", "balance", event.target.value)} /><span className="order-ticket__protection-label">Balance</span><input aria-label="Take profit balance" inputMode="decimal" value={takeProfitValues.balance} disabled={!takeProfitEnabled || !calculatorReady} onChange={(event) => updateProtection("TAKE_PROFIT", "balance", event.target.value)} />
        <input aria-label="Stop loss profit" inputMode="decimal" value={stopLossValues.profit} disabled={!stopLossEnabled || !calculatorReady} onChange={(event) => updateProtection("STOP_LOSS", "profit", event.target.value)} /><span className="order-ticket__protection-label">Profit</span><input aria-label="Take profit profit" inputMode="decimal" value={takeProfitValues.profit} disabled={!takeProfitEnabled || !calculatorReady} onChange={(event) => updateProtection("TAKE_PROFIT", "profit", event.target.value)} />
      </div>
      {!calculatorReady && <small className="order-ticket__calculator-unavailable">Protection calculator unavailable: complete provider instrument and account evidence is required.</small>}
      <div className="order-ticket__advanced"><label className="order-ticket__check"><input type="checkbox" disabled /><span>Trailing stop</span></label><label className="order-ticket__check"><input type="checkbox" disabled /><span>Break-even</span></label></div>
      <label className="order-ticket__comment"><span>Comment</span><textarea aria-label="Comment" disabled title="Comments are not supported by the current Trading contract." /></label>
      <label className="order-ticket__time-in-force"><span>Time in force</span><select value={timeInForce} onChange={(event) => setTimeInForce(event.target.value)}><option value="">Authority default</option>{constraints?.supported_time_in_force.map((value) => <option key={value}>{value}</option>)}</select></label>
    </div>
    {loading && <p role="status">Loading authoritative market and instrument evidence…</p>}{validation && !loading && <p role="status">{validation}</p>}{symbolUniverseError && <p role="alert">{symbolUniverseError}</p>}{strategyError && <p role="alert">{strategyError}</p>}{error && <p role="alert">{error}</p>}{result && <p role="status">{result}</p>}
    {!confirming ? <button className="order-ticket__submit" type="button" disabled={Boolean(validation) || loading} onClick={() => orderConfirmationRequired ? setConfirming(true) : void submit()}>Place order</button> : <div className="order-ticket__confirmation" role="alertdialog" aria-modal="true"><p>Confirm {side} {quantity} {constraints?.quantity_unit} {symbol} as {orderType}?</p><button type="button" onClick={() => setConfirming(false)}>Back</button><button type="button" onClick={() => void submit()}>Confirm and submit</button></div>}{!embedded && <button className="order-ticket__close" type="button" onClick={closeOrderTicket}>Close ticket</button>}
  </div></section>;
  return embedded ? content : <div className="modal-overlay" role="presentation">{content}</div>;
}
