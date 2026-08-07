/** Governed Portfolio workflow presentation. */

"use client";

import { useState, type ReactNode } from "react";

import { ApiClientError, apiClients } from "@/clients";
import type { PortfolioDefinitionBody, PortfolioRecord } from "@/clients/portfolio";

/** Props accepted by `PortfolioView`. */
export interface PortfolioViewProps {
  className?: string;
}

const DEFAULT_DEFINITION = JSON.stringify(
  {
    objective: "balanced-risk",
    components: ["strategy-alpha", "strategy-beta"],
  },
  null,
  2
);

/** Register and inspect immutable Portfolio definitions without deciding approval. */
export function PortfolioView({ className }: PortfolioViewProps = {}): ReactNode {
  const [portfolioId, setPortfolioId] = useState("portfolio-alpha");
  const [portfolioVersion, setPortfolioVersion] = useState("v1");
  const [definitionText, setDefinitionText] = useState(DEFAULT_DEFINITION);
  const [canonicalHash, setCanonicalHash] = useState("");
  const [result, setResult] = useState<PortfolioRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function register(): Promise<void> {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const definition = JSON.parse(definitionText) as Record<string, unknown>;
      const body: PortfolioDefinitionBody = {
        contract_version: "v1",
        schema_id: "portfolio.definition.v1",
        portfolio_id: portfolioId,
        portfolio_version: portfolioVersion,
        scope: { environment: "simulation" },
        definition,
        canonical_hash: canonicalHash,
      };
      const response = await apiClients.portfolio.registerDefinition(
        portfolioId,
        body
      );
      if (response.status === "error") setError(response.error.message);
      else setResult(response.data);
    } catch (cause) {
      if (cause instanceof SyntaxError) setError("Definition must be valid JSON");
      else setError(cause instanceof ApiClientError ? cause.message : "unavailable");
    } finally {
      setLoading(false);
    }
  }

  async function read(): Promise<void> {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClients.portfolio.definition(
        portfolioId,
        portfolioVersion
      );
      if (response.status === "error") setError(response.error.message);
      else setResult(response.data);
    } catch (cause) {
      setError(cause instanceof ApiClientError ? cause.message : "unavailable");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className={`workflow-portfolio ${className ?? ""}`.trim()}
      role="region"
      aria-label="Portfolio"
    >
      <p>
        Definition management only. Risk approval and Trading execution remain
        separate governed actions.
      </p>
      <label>
        Portfolio ID
        <input value={portfolioId} onChange={(event) => setPortfolioId(event.target.value)} />
      </label>
      <label>
        Version
        <input value={portfolioVersion} onChange={(event) => setPortfolioVersion(event.target.value)} />
      </label>
      <label>
        Canonical SHA-256
        <input value={canonicalHash} onChange={(event) => setCanonicalHash(event.target.value)} />
      </label>
      <label>
        Immutable definition
        <textarea
          aria-label="Immutable definition"
          value={definitionText}
          onChange={(event) => setDefinitionText(event.target.value)}
          rows={8}
        />
      </label>
      <button type="button" onClick={() => void register()} disabled={loading}>
        Register definition
      </button>
      <button type="button" onClick={() => void read()} disabled={loading}>
        Read definition
      </button>
      {loading && <span role="status">loading…</span>}
      {error && <span role="alert">{error}</span>}
      {result && <pre aria-label="Portfolio definition result">{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
