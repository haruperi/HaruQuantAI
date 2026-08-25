import React from "react";
import type { CapabilityPresentationState } from "../../runtime/composition_bridge";

export interface CapabilityStateViewProps {
  capabilityId: string;
  state: CapabilityPresentationState;
}

const STATE_METADATA: Record<
  CapabilityPresentationState,
  { label: string; symbol: string; className: string }
> = {
  ready: { label: "Ready", symbol: "[✓]", className: "state-ready" },
  loading: { label: "Loading...", symbol: "[...]", className: "state-loading" },
  degraded: { label: "Degraded", symbol: "[!]", className: "state-degraded" },
  unavailable: { label: "Unavailable", symbol: "[x]", className: "state-unavailable" },
  disabled: { label: "Disabled", symbol: "[-]", className: "state-disabled" },
  unauthorized: { label: "Unauthorized", symbol: "[🔒]", className: "state-unauthorized" },
  incompatible: { label: "Incompatible", symbol: "[⊘]", className: "state-incompatible" },
};

export const CapabilityStateView: React.FC<CapabilityStateViewProps> = ({
  capabilityId,
  state,
}) => {
  const meta = STATE_METADATA[state] ?? STATE_METADATA.unavailable;

  return (
    <div
      className={`capability-state-badge ${meta.className}`}
      role="status"
      aria-label={`Capability ${capabilityId} is ${meta.label}`}
      data-testid={`capability-badge-${capabilityId}`}
    >
      <span className="state-symbol" aria-hidden="true">
        {meta.symbol}
      </span>
      <span className="state-name">{capabilityId}</span>
      <span className="state-status-text">({meta.label})</span>
    </div>
  );
};
