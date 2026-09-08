"use client";

import React, { useMemo, useState } from "react";
import { AlertCircle, AlertTriangle, CheckCircle, Info, ShieldAlert } from "lucide-react";

import type {
  ConsequentialAction,
  ConsequentialReviewResult,
  DraftDiffEntry,
  ValidationSummary,
} from "./contracts";

export interface DraftReviewProps {
  readonly title?: string;
  readonly diffs?: readonly DraftDiffEntry[];
  readonly validation?: ValidationSummary;
  readonly action?: ConsequentialAction;
  readonly currentAuthoritativeHash?: string;
  readonly currentAuthoritativeRevision?: number | string;
  readonly onConfirm?: () => void;
  readonly onCancel?: () => void;
  readonly onDiscardDraft?: () => void;
  readonly isLoading?: boolean;
}

export function DraftReview({
  title = "Review Changes & Consequential Action",
  diffs = [],
  validation,
  action,
  currentAuthoritativeHash,
  currentAuthoritativeRevision,
  onConfirm,
  onCancel,
  onDiscardDraft,
  isLoading = false,
}: DraftReviewProps): React.JSX.Element {
  const [confirmationInput, setConfirmationInput] = useState("");

  // Determine consequential review validity
  const reviewResult: ConsequentialReviewResult = useMemo(() => {
    if (!action) {
      return { status: "VALID", canExecute: true };
    }

    // Security check: Model prose cannot manufacture executable action without authorization
    if (action.modelProse && action.isServerAuthorized === false) {
      return {
        status: "PROSE_REJECTED",
        reason:
          "Unverified model prose explanation cannot manufacture executable server actions.",
        canExecute: false,
      };
    }

    // Concurrency check: Candidate hash and expected revision must match authoritative source
    if (
      currentAuthoritativeHash &&
      action.candidateHash !== currentAuthoritativeHash
    ) {
      return {
        status: "INVALIDATED",
        reason:
          "Scope or candidate hash has changed since review preparation. Action review is invalidated.",
        canExecute: false,
      };
    }

    if (
      currentAuthoritativeRevision !== undefined &&
      String(action.expectedRevision) !== String(currentAuthoritativeRevision)
    ) {
      return {
        status: "STALE",
        reason: `Target revision conflict: expected revision ${action.expectedRevision}, but current revision is ${currentAuthoritativeRevision}.`,
        canExecute: false,
      };
    }

    return { status: "VALID", canExecute: true };
  }, [action, currentAuthoritativeHash, currentAuthoritativeRevision]);

  const isIrreversible = action?.reversibility === "IRREVERSIBLE";
  const requiredPhrase = action?.confirmationPhrase ?? "CONFIRM";
  const isPhraseConfirmed =
    !isIrreversible || confirmationInput.trim().toUpperCase() === requiredPhrase.toUpperCase();

  const canConfirm =
    reviewResult.canExecute &&
    (validation ? validation.isValid : true) &&
    isPhraseConfirmed &&
    !isLoading;

  return (
    <div className="draft-review-container" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* Title */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 600, color: "#fff" }}>{title}</h3>
        {action && (
          <span
            style={{
              fontSize: "12px",
              padding: "2px 8px",
              borderRadius: "4px",
              fontWeight: 500,
              backgroundColor:
                action.reversibility === "IRREVERSIBLE"
                  ? "rgba(248, 81, 73, 0.15)"
                  : action.reversibility === "REVERSIBLE_WITH_PENALTY"
                    ? "rgba(210, 153, 34, 0.15)"
                    : "rgba(46, 160, 67, 0.15)",
              color:
                action.reversibility === "IRREVERSIBLE"
                  ? "#f85149"
                  : action.reversibility === "REVERSIBLE_WITH_PENALTY"
                    ? "#d29922"
                    : "#3fb950",
              border: `1px solid ${
                action.reversibility === "IRREVERSIBLE"
                  ? "#f85149"
                  : action.reversibility === "REVERSIBLE_WITH_PENALTY"
                    ? "#d29922"
                    : "#2ea043"
              }`,
            }}
          >
            {action.reversibility}
          </span>
        )}
      </div>

      {/* Invalidated / Stale Warning Banner */}
      {!reviewResult.canExecute && (
        <div
          role="alert"
          aria-live="assertive"
          className="review-invalidation-banner"
          style={{
            padding: "12px 16px",
            borderRadius: "6px",
            backgroundColor: "rgba(248, 81, 73, 0.12)",
            border: "1px solid #f85149",
            color: "#f85149",
            display: "flex",
            alignItems: "flex-start",
            gap: "10px",
            fontSize: "13px",
          }}
        >
          <ShieldAlert size={18} style={{ flexShrink: 0, marginTop: "2px" }} />
          <div>
            <strong>Review Invalidated ({reviewResult.status}):</strong>
            <p style={{ margin: "4px 0 0 0" }}>{reviewResult.reason}</p>
          </div>
        </div>
      )}

      {/* Consequential Action Scope Card */}
      {action && (
        <div
          className="consequential-action-scope"
          style={{
            padding: "14px 16px",
            backgroundColor: "#21262d",
            border: "1px solid #30363d",
            borderRadius: "6px",
            fontSize: "13px",
          }}
        >
          <div style={{ marginBottom: "10px", paddingBottom: "8px", borderBottom: "1px solid #30363d" }}>
            <span style={{ fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px", color: "#8b949e", fontWeight: 600 }}>Action:</span>
            <div style={{ fontSize: "14px", fontWeight: 600, color: "#58a6ff", marginTop: "2px" }}>
              {action.title}
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "8px" }}>
            <div>
              <span style={{ color: "#8b949e" }}>Target Object:</span>
              <div style={{ fontWeight: 600, color: "#fff", marginTop: "2px" }}>
                {action.target.name} ({action.target.type})
              </div>
              <div style={{ fontSize: "11px", color: "#8b949e" }}>ID: {action.target.id}</div>
            </div>
            <div>
              <span style={{ color: "#8b949e" }}>Affected Records:</span>
              <div style={{ fontWeight: 600, color: "#fff", marginTop: "2px" }}>
                {action.affectedCount.toLocaleString()} {action.affectedCount === 1 ? "item" : "items"}
              </div>
              <div style={{ fontSize: "11px", color: "#8b949e" }}>Revision: {action.expectedRevision}</div>
            </div>
          </div>

          {action.dependencies.length > 0 && (
            <div style={{ marginTop: "8px", paddingTop: "8px", borderTop: "1px solid #30363d" }}>
              <span style={{ color: "#8b949e" }}>Dependencies Affected:</span>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "4px" }}>
                {action.dependencies.map((dep) => (
                  <span
                    key={dep}
                    style={{
                      fontSize: "11px",
                      background: "#161b22",
                      border: "1px solid #30363d",
                      padding: "2px 6px",
                      borderRadius: "4px",
                      color: "#c9d1d9",
                    }}
                  >
                    {dep}
                  </span>
                ))}
              </div>
            </div>
          )}

          {action.retainedState.length > 0 && (
            <div style={{ marginTop: "8px", paddingTop: "8px", borderTop: "1px solid #30363d" }}>
              <span style={{ color: "#8b949e" }}>Retained State:</span>
              <div style={{ fontSize: "12px", color: "#7ee787", marginTop: "2px" }}>
                {action.retainedState.join(", ")}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Model Prose Explanation Card */}
      {action?.modelProse && (
        <div
          className="model-prose-card"
          style={{
            padding: "10px 14px",
            backgroundColor: "#161b22",
            border: "1px solid #30363d",
            borderRadius: "6px",
            fontSize: "12px",
            color: "#8b949e",
          }}
        >
          <div style={{ fontWeight: 500, color: "#58a6ff", marginBottom: "4px" }}>
            Assistant Review Summary
          </div>
          <div>{action.modelProse}</div>
        </div>
      )}

      {/* Form Diffs Table */}
      {diffs.length > 0 && (
        <div className="draft-diffs-section">
          <div style={{ fontSize: "13px", fontWeight: 600, color: "#c9d1d9", marginBottom: "8px" }}>
            Field Modifications ({diffs.filter((d) => d.isDirty).length} dirty)
          </div>
          <div
            style={{
              border: "1px solid #30363d",
              borderRadius: "6px",
              overflow: "hidden",
              fontSize: "12px",
            }}
          >
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "140px 1fr 1fr",
                padding: "8px 12px",
                backgroundColor: "#161b22",
                borderBottom: "1px solid #30363d",
                fontWeight: 600,
                color: "#8b949e",
              }}
            >
              <div>Field</div>
              <div>Original</div>
              <div>Proposed Draft</div>
            </div>
            {diffs.map((diff) => (
              <div
                key={diff.field}
                style={{
                  display: "grid",
                  gridTemplateColumns: "140px 1fr 1fr",
                  padding: "8px 12px",
                  borderBottom: "1px solid #21262d",
                  backgroundColor: diff.isDirty ? "rgba(56, 139, 253, 0.05)" : "transparent",
                  color: diff.isDirty ? "#fff" : "#8b949e",
                }}
              >
                <div style={{ fontWeight: diff.isDirty ? 600 : 400 }}>{diff.label}</div>
                <div style={{ color: "#8b949e", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {diff.format ? diff.format(diff.originalValue) : String(diff.originalValue ?? "—")}
                </div>
                <div
                  style={{
                    color: diff.isDirty ? "#58a6ff" : "#8b949e",
                    fontWeight: diff.isDirty ? 500 : 400,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {diff.format ? diff.format(diff.draftValue) : String(diff.draftValue ?? "—")}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Validation Summary (Client Hints vs Authoritative Errors) */}
      {validation && (validation.errors.length > 0 || validation.warnings.length > 0 || validation.hints.length > 0) && (
        <div className="validation-summary-section" style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          {validation.errors.map((err) => (
            <div
              key={`${err.source}-${err.field}`}
              role="alert"
              style={{
                fontSize: "12px",
                padding: "6px 10px",
                borderRadius: "4px",
                backgroundColor: "rgba(248, 81, 73, 0.1)",
                border: "1px solid #f85149",
                color: "#f85149",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              <AlertCircle size={14} />
              <span>
                <strong>{err.source === "authoritative" ? "Server Error" : "Validation"} ({err.field}):</strong>{" "}
                {err.message}
              </span>
            </div>
          ))}

          {validation.warnings.map((warn) => (
            <div
              key={`${warn.source}-${warn.field}`}
              style={{
                fontSize: "12px",
                padding: "6px 10px",
                borderRadius: "4px",
                backgroundColor: "rgba(210, 153, 34, 0.1)",
                border: "1px solid #d29922",
                color: "#d29922",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              <AlertTriangle size={14} />
              <span>
                <strong>Warning ({warn.field}):</strong> {warn.message}
              </span>
            </div>
          ))}

          {validation.hints.map((hint) => (
            <div
              key={`${hint.source}-${hint.field}`}
              style={{
                fontSize: "12px",
                padding: "6px 10px",
                borderRadius: "4px",
                backgroundColor: "rgba(88, 166, 255, 0.1)",
                border: "1px solid #58a6ff",
                color: "#58a6ff",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              <Info size={14} />
              <span>
                <strong>Hint ({hint.field}):</strong> {hint.message}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Irreversible Confirmation Guard Input */}
      {isIrreversible && (
        <div
          className="irreversible-confirmation-box"
          style={{
            padding: "12px",
            backgroundColor: "rgba(248, 81, 73, 0.08)",
            border: "1px solid #f85149",
            borderRadius: "6px",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
          }}
        >
          <label
            htmlFor="confirmation-phrase-input"
            style={{ fontSize: "13px", fontWeight: 600, color: "#f85149" }}
          >
            Type &quot;{requiredPhrase}&quot; to confirm this irreversible operation:
          </label>
          <input
            id="confirmation-phrase-input"
            type="text"
            value={confirmationInput}
            onChange={(e) => setConfirmationInput(e.target.value)}
            placeholder={requiredPhrase}
            style={{
              padding: "6px 10px",
              backgroundColor: "#161b22",
              border: "1px solid #30363d",
              borderRadius: "4px",
              color: "#fff",
              fontSize: "13px",
              outline: "none",
            }}
          />
        </div>
      )}

      {/* Action Footer Bar */}
      <footer
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          paddingTop: "12px",
          borderTop: "1px solid #30363d",
          marginTop: "4px",
        }}
      >
        <div>
          {onDiscardDraft && diffs.some((d) => d.isDirty) && (
            <button
              type="button"
              onClick={onDiscardDraft}
              style={{
                background: "none",
                border: "none",
                color: "#8b949e",
                fontSize: "13px",
                cursor: "pointer",
                padding: "6px 8px",
              }}
            >
              Discard Draft
            </button>
          )}
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              style={{
                background: "#21262d",
                border: "1px solid #30363d",
                color: "#c9d1d9",
                padding: "6px 14px",
                borderRadius: "4px",
                fontSize: "13px",
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
          )}

          {(onConfirm || action) && (
            <button
              type="button"
              disabled={!canConfirm || !onConfirm}
              onClick={onConfirm}
              style={{
                background: !canConfirm
                  ? "#21262d"
                  : isIrreversible
                    ? "#b62324"
                    : "#1f6feb",
                border: `1px solid ${
                  !canConfirm
                    ? "#30363d"
                    : isIrreversible
                      ? "#f85149"
                      : "#388bfd"
                }`,
                color: !canConfirm ? "#8b949e" : "#fff",
                padding: "6px 16px",
                borderRadius: "4px",
                fontSize: "13px",
                fontWeight: 600,
                cursor: !canConfirm ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              {isLoading ? (
                "Executing…"
              ) : (
                <>
                  <CheckCircle size={14} />
                  <span>{isIrreversible ? "Confirm Irreversible Action" : "Confirm & Save"}</span>
                </>
              )}
            </button>
          )}
        </div>
      </footer>
    </div>
  );
}
