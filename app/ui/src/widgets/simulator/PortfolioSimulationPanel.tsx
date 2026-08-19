/**
 * Portfolio simulation destination (FEAT-UI-31).
 *
 * A portfolio simulation is an explicitly configured destination, never an
 * inference. Running several symbols in one batch produces several independent
 * runs, not a portfolio: aggregating them would silently assume a weighting,
 * a rebalancing rule, and an FX conversion nobody stated.
 *
 * This panel therefore requires every component, weight, risk budget, window,
 * account currency, and FX evidence reference before it will submit.
 */

"use client";

import { useCallback, useMemo, useState, type ReactNode } from "react";

/** Exact refusal shown when a batch is mistaken for a portfolio. */
export const NO_PORTFOLIO_INFERENCE =
  "A multi-symbol batch is a set of independent runs, not a portfolio. " +
  "Configure a portfolio simulation explicitly to aggregate them.";

/** Maximum components one portfolio simulation accepts. */
export const MAX_PORTFOLIO_COMPONENTS = 32;

/** One explicitly configured portfolio component. */
export interface PortfolioComponent {
  symbol: string;
  strategyId: string;
  weight: string;
  riskBudget: string;
}

/** Complete portfolio configuration ready for submission. */
export interface PortfolioSimulationRequest {
  components: PortfolioComponent[];
  start: string;
  end: string;
  account_currency: string;
  fx_evidence_ref: string;
}

/** Parse a decimal weight, returning null when it is not exact. */
function decimal(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Props accepted by `PortfolioSimulationPanel`. */
export interface PortfolioSimulationPanelProps {
  onSubmit?: (request: PortfolioSimulationRequest) => void;
  className?: string;
}

/** Explicit portfolio configuration and submission. */
export function PortfolioSimulationPanel({
  onSubmit,
  className = "",
}: PortfolioSimulationPanelProps): ReactNode {
  const [components, setComponents] = useState<PortfolioComponent[]>([
    { symbol: "", strategyId: "", weight: "", riskBudget: "" },
  ]);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [currency, setCurrency] = useState("");
  const [fxEvidence, setFxEvidence] = useState("");

  const updateComponent = useCallback(
    (index: number, patch: Partial<PortfolioComponent>) => {
      setComponents((current) =>
        current.map((item, position) =>
          position === index ? { ...item, ...patch } : item,
        ),
      );
    },
    [],
  );

  const addComponent = useCallback(() => {
    setComponents((current) =>
      current.length >= MAX_PORTFOLIO_COMPONENTS
        ? current
        : [...current, { symbol: "", strategyId: "", weight: "", riskBudget: "" }],
    );
  }, []);

  /** Every blocking problem in the current configuration. */
  const problems = useMemo(() => {
    const found: string[] = [];

    components.forEach((component, index) => {
      const position = index + 1;
      if (!component.symbol.trim()) {
        found.push(`Component ${position} needs a symbol.`);
      }
      if (!component.strategyId.trim()) {
        found.push(`Component ${position} needs a strategy.`);
      }
      if (decimal(component.weight) === null) {
        found.push(`Component ${position} needs an explicit weight.`);
      }
      if (decimal(component.riskBudget) === null) {
        found.push(`Component ${position} needs an explicit risk budget.`);
      }
    });

    const weights = components.map((item) => decimal(item.weight));
    if (weights.every((weight) => weight !== null)) {
      const total = weights.reduce<number>(
        (sum, weight) => sum + (weight ?? 0),
        0,
      );
      if (Math.abs(total - 1) > 1e-9) {
        found.push("Component weights must sum to exactly 1.");
      }
    }

    if (!start || !end) {
      found.push("A portfolio simulation needs an explicit window.");
    } else if (start > end) {
      found.push("The start date must not be after the end date.");
    }
    if (!currency.trim()) {
      found.push("A portfolio simulation needs an explicit account currency.");
    }
    if (!fxEvidence.trim()) {
      found.push("A portfolio simulation needs an FX evidence reference.");
    }

    return found;
  }, [components, start, end, currency, fxEvidence]);

  const submit = useCallback(() => {
    if (problems.length > 0) return;
    onSubmit?.({
      components: components.map((component) => ({
        symbol: component.symbol.trim(),
        strategyId: component.strategyId.trim(),
        weight: component.weight.trim(),
        riskBudget: component.riskBudget.trim(),
      })),
      start,
      end,
      account_currency: currency.trim(),
      fx_evidence_ref: fxEvidence.trim(),
    });
  }, [problems, onSubmit, components, start, end, currency, fxEvidence]);

  return (
    <section
      className={`simulation-portfolio ${className}`.trim()}
      aria-label="Portfolio simulation"
    >
      <h4>Portfolio simulation</h4>
      <p role="note" className="simulation-portfolio__note">
        {NO_PORTFOLIO_INFERENCE}
      </p>

      <fieldset>
        <legend>Components</legend>
        {components.map((component, index) => (
          <div key={index} className="simulation-portfolio__component">
            <label htmlFor={`portfolio-symbol-${index}`}>
              Component {index + 1} symbol
            </label>
            <input
              id={`portfolio-symbol-${index}`}
              value={component.symbol}
              onChange={(event) =>
                updateComponent(index, { symbol: event.target.value })
              }
            />

            <label htmlFor={`portfolio-strategy-${index}`}>
              Component {index + 1} strategy
            </label>
            <input
              id={`portfolio-strategy-${index}`}
              value={component.strategyId}
              onChange={(event) =>
                updateComponent(index, { strategyId: event.target.value })
              }
            />

            <label htmlFor={`portfolio-weight-${index}`}>
              Component {index + 1} weight
            </label>
            <input
              id={`portfolio-weight-${index}`}
              value={component.weight}
              onChange={(event) =>
                updateComponent(index, { weight: event.target.value })
              }
            />

            <label htmlFor={`portfolio-risk-${index}`}>
              Component {index + 1} risk budget
            </label>
            <input
              id={`portfolio-risk-${index}`}
              value={component.riskBudget}
              onChange={(event) =>
                updateComponent(index, { riskBudget: event.target.value })
              }
            />
          </div>
        ))}
        <button
          type="button"
          onClick={addComponent}
          disabled={components.length >= MAX_PORTFOLIO_COMPONENTS}
        >
          Add component
        </button>
      </fieldset>

      <fieldset>
        <legend>Window and currency</legend>
        <label htmlFor="portfolio-start">Start</label>
        <input
          id="portfolio-start"
          type="date"
          value={start}
          onChange={(event) => setStart(event.target.value)}
        />

        <label htmlFor="portfolio-end">End</label>
        <input
          id="portfolio-end"
          type="date"
          value={end}
          onChange={(event) => setEnd(event.target.value)}
        />

        <label htmlFor="portfolio-currency">Account currency</label>
        <input
          id="portfolio-currency"
          value={currency}
          onChange={(event) => setCurrency(event.target.value)}
        />

        <label htmlFor="portfolio-fx">FX evidence reference</label>
        <input
          id="portfolio-fx"
          value={fxEvidence}
          onChange={(event) => setFxEvidence(event.target.value)}
        />
      </fieldset>

      {problems.length > 0 ? (
        <ul role="alert" aria-label="Portfolio validation problems">
          {problems.map((problem) => (
            <li key={problem}>{problem}</li>
          ))}
        </ul>
      ) : null}

      <button type="button" onClick={submit} disabled={problems.length > 0}>
        Submit portfolio simulation
      </button>
    </section>
  );
}
