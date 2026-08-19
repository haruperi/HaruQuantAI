/**
 * Expectancy page (FEAT-UI-28, plan §10.19).
 *
 * Displays the approved expectancy profile, its lifecycle state, and its
 * eligibility evidence. Research remains the state-machine authority; permitted
 * reviewers may submit a governed transition for server validation.
 */

"use client";

import Link from "next/link";
import { useState, type ReactNode } from "react";

import { ApiClientError, apiClients } from "@/clients";

import { Badge, KeyValues, RecordTable, Section } from "./evidence";
import { EvidenceGate } from "./ResearchRunStatus";
import { asText, evidenceRecord } from "./research-selectors";
import { useExpectancy } from "./use-research";

/** Approved expectancy profile and governance state. */
export function ResearchExpectancy(): ReactNode {
  const [profileId, setProfileId] = useState("");
  const [strategyRef, setStrategyRef] = useState("");
  const [query, setQuery] = useState<{
    profileId?: string;
    strategyRef?: string;
  }>({});
  const expectancy = useExpectancy(query);
  const profile = expectancy.data?.profile ?? null;
  const [targetState, setTargetState] = useState("under_review");
  const [decision, setDecision] = useState("");
  const [reason, setReason] = useState("");
  const [transitioning, setTransitioning] = useState(false);
  const [transitionError, setTransitionError] = useState<string | null>(null);
  const [transitionMessage, setTransitionMessage] = useState<string | null>(
    null,
  );
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createMessage, setCreateMessage] = useState<string | null>(null);

  async function createProfile(form: HTMLFormElement): Promise<void> {
    const values = new FormData(form);
    setCreating(true);
    setCreateError(null);
    setCreateMessage(null);
    try {
      const response = await apiClients.research.createExpectancy({
        run_id: String(values.get("run_id") ?? "").trim(),
        exact_version: String(values.get("exact_version") ?? "").trim(),
        strategy_ref: String(values.get("strategy_ref") ?? "").trim(),
        regimes: String(values.get("regimes") ?? "")
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean),
        sessions: String(values.get("sessions") ?? "")
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean),
        sample_from_utc: new Date(
          String(values.get("sample_from")),
        ).toISOString(),
        sample_to_utc: new Date(String(values.get("sample_to"))).toISOString(),
        sample_size: Number(values.get("sample_size")),
        out_of_sample_status: String(values.get("oos")) as
          "in_sample" | "out_of_sample" | "walk_forward",
        win_rate: Number(values.get("win_rate")),
        avg_win_r: Number(values.get("avg_win_r")),
        avg_loss_r: Number(values.get("avg_loss_r")),
        expected_value_r: Number(values.get("expected_value_r")),
        max_drawdown_r: Number(values.get("max_drawdown_r")),
        min_reward_risk: Number(values.get("min_reward_risk")),
      });
      if (response.status === "error") {
        setCreateError(response.error.message);
        return;
      }
      const createdId = asText(response.data.profile?.profile_id);
      setCreateMessage(`Draft profile ${createdId ?? "created"}.`);
      if (createdId) {
        setProfileId(createdId);
        setQuery({ profileId: createdId });
      }
    } catch (cause) {
      setCreateError(
        cause instanceof ApiClientError
          ? cause.message
          : "Profile creation unavailable",
      );
    } finally {
      setCreating(false);
    }
  }

  async function transition(): Promise<void> {
    const selectedProfileId = asText(profile?.profile_id);
    if (!selectedProfileId) return;
    setTransitioning(true);
    setTransitionError(null);
    setTransitionMessage(null);
    try {
      const response = await apiClients.research.transitionExpectancy(
        selectedProfileId,
        {
          target_state: targetState as
            | "draft"
            | "under_review"
            | "approved"
            | "suspended"
            | "expired"
            | "revoked",
          decision: decision.trim(),
          reason: reason.trim(),
        },
      );
      if (response.status === "error") {
        setTransitionError(response.error.message);
        return;
      }
      setTransitionMessage(`Transitioned to ${targetState}.`);
      setDecision("");
      setReason("");
      expectancy.reload();
    } catch (cause) {
      setTransitionError(
        cause instanceof ApiClientError
          ? cause.message
          : "Transition unavailable",
      );
    } finally {
      setTransitioning(false);
    }
  }

  return (
    <div className="research-page">
      <header className="research-page__head">
        <p className="research-eyebrow">Research workbench</p>
        <h1>Expectancy</h1>
        <p>
          The approved expectancy profile Research governs. This page reports
          state and lets authorized reviewers request a Research-governed
          transition.
        </p>
        <div className="research-links">
          <Link className="research-button" href="/workstation/research">
            Back to ledger
          </Link>
          <Link className="research-button" href="/workstation/research/drift">
            Drift monitor
          </Link>
        </div>
      </header>

      {expectancy.data?.transition_permitted ? (
        <Section
          title="Create draft profile"
          description="Bind explicit measured expectancy statistics to an owned completed run. Creation records a draft; it never approves it."
        >
          <form
            className="research-form-grid"
            onSubmit={(event) => {
              event.preventDefault();
              void createProfile(event.currentTarget);
            }}
          >
            {[
              ["run_id", "Completed run id"],
              ["exact_version", "Exact version"],
              ["strategy_ref", "Strategy ref"],
              ["regimes", "Regimes (comma separated)"],
              ["sessions", "Sessions (comma separated)"],
            ].map(([name, label]) => (
              <label key={name} className="research-field">
                {label}
                <input
                  name={name}
                  required={!["regimes", "sessions"].includes(name)}
                />
              </label>
            ))}
            <label className="research-field">
              Sample from
              <input name="sample_from" type="datetime-local" required />
            </label>
            <label className="research-field">
              Sample to
              <input name="sample_to" type="datetime-local" required />
            </label>
            <label className="research-field">
              Evidence status
              <select name="oos" defaultValue="walk_forward">
                <option value="in_sample">In sample</option>
                <option value="out_of_sample">Out of sample</option>
                <option value="walk_forward">Walk forward</option>
              </select>
            </label>
            {[
              ["sample_size", "Sample size", "1"],
              ["win_rate", "Win rate", "0.01"],
              ["avg_win_r", "Average win (R)", "0.01"],
              ["avg_loss_r", "Average loss (R)", "0.01"],
              ["expected_value_r", "Expected value (R)", "0.01"],
              ["max_drawdown_r", "Max drawdown (R)", "0.01"],
              ["min_reward_risk", "Minimum reward/risk", "0.01"],
            ].map(([name, label, step]) => (
              <label key={name} className="research-field">
                {label}
                <input
                  name={name}
                  type="number"
                  step={step}
                  min={name === "expected_value_r" ? undefined : 0}
                  required
                />
              </label>
            ))}
            <button
              className="research-button"
              type="submit"
              disabled={creating}
            >
              {creating ? "Creating…" : "Create draft"}
            </button>
          </form>
          {createError ? (
            <p role="alert" className="research-error">
              {createError}
            </p>
          ) : null}
          {createMessage ? (
            <p role="status" className="research-note">
              {createMessage}
            </p>
          ) : null}
        </Section>
      ) : null}

      <Section
        title="Profile selection"
        description="Look up by governance identity, or by the strategy a profile covers."
        actions={
          <form
            className="research-inline-form"
            onSubmit={(event) => {
              event.preventDefault();
              setQuery({
                profileId: profileId.trim() || undefined,
                strategyRef: strategyRef.trim() || undefined,
              });
            }}
          >
            <label className="research-inline-field">
              Profile id
              <input
                value={profileId}
                onChange={(event) => setProfileId(event.target.value)}
              />
            </label>
            <label className="research-inline-field">
              Strategy ref
              <input
                value={strategyRef}
                onChange={(event) => setStrategyRef(event.target.value)}
              />
            </label>
            <button type="submit" className="research-button">
              Load
            </button>
          </form>
        }
      >
        <EvidenceGate
          loading={expectancy.loading}
          error={expectancy.error}
          reload={expectancy.reload}
          ready={expectancy.data !== null}
          loadingLabel="Loading expectancy evidence…"
        >
          {expectancy.data?.available && profile ? (
            <>
              <KeyValues
                columns={4}
                items={[
                  ["Profile id", asText(profile.profile_id) ?? "—"],
                  ["Version", asText(profile.version) ?? "—"],
                  [
                    "Lifecycle state",
                    <Badge key="l" tone="neutral">
                      {asText(profile.lifecycle_state) ??
                        asText(profile.state) ??
                        "—"}
                    </Badge>,
                  ],
                  [
                    "Eligibility",
                    <Badge
                      key="e"
                      tone={profile.eligible === true ? "positive" : "warning"}
                    >
                      {profile.eligible === true
                        ? "eligible"
                        : (asText(profile.eligibility) ?? "not eligible")}
                    </Badge>,
                  ],
                  [
                    "Min reward/risk override",
                    asText(profile.min_reward_risk_override) ?? "none approved",
                  ],
                  ["Strategy ref", asText(profile.strategy_ref) ?? "—"],
                  [
                    "Transition permitted",
                    <Badge
                      key="t"
                      tone={
                        expectancy.data.transition_permitted
                          ? "positive"
                          : "unknown"
                      }
                    >
                      {expectancy.data.transition_permitted
                        ? "caller holds research:govern"
                        : "caller lacks research:govern"}
                    </Badge>,
                  ],
                ]}
              />
              {expectancy.data.transition_permitted ? (
                <Section
                  title="Governance transition"
                  description="Research validates the lifecycle edge and records the review atomically."
                >
                  <form
                    className="research-inline-form"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void transition();
                    }}
                  >
                    <label className="research-inline-field">
                      Target state
                      <select
                        value={targetState}
                        onChange={(event) => setTargetState(event.target.value)}
                      >
                        <option value="draft">Draft</option>
                        <option value="under_review">Under review</option>
                        <option value="approved">Approved</option>
                        <option value="suspended">Suspended</option>
                        <option value="expired">Expired</option>
                        <option value="revoked">Revoked</option>
                      </select>
                    </label>
                    <label className="research-inline-field">
                      Decision
                      <input
                        required
                        maxLength={100}
                        value={decision}
                        onChange={(event) => setDecision(event.target.value)}
                      />
                    </label>
                    <label className="research-inline-field">
                      Reason
                      <input
                        required
                        maxLength={500}
                        value={reason}
                        onChange={(event) => setReason(event.target.value)}
                      />
                    </label>
                    <button
                      type="submit"
                      className="research-button"
                      disabled={transitioning}
                    >
                      {transitioning ? "Transitioning…" : "Apply transition"}
                    </button>
                  </form>
                  {transitionError ? (
                    <p className="research-error" role="alert">
                      {transitionError}
                    </p>
                  ) : null}
                  {transitionMessage ? (
                    <p className="research-success" role="status">
                      {transitionMessage}
                    </p>
                  ) : null}
                </Section>
              ) : null}
              <Section
                title="Evidence and reasons"
                description="The eligibility evidence Research recorded with the profile."
              >
                <RecordTable
                  record={evidenceRecord(profile, "evidence") ?? profile}
                  emptyLabel="No evidence branch was recorded."
                />
              </Section>
              <Section
                title="Review history"
                description="Recorded governance reviews, newest last."
              >
                <RecordTable
                  record={evidenceRecord(profile, "review_history")}
                  emptyLabel="No review history was recorded."
                />
              </Section>
            </>
          ) : (
            <div className="research-empty" role="status">
              <Badge tone="unknown">Unavailable</Badge>
              <p>
                {asText(expectancy.data?.reason) === "PROFILE_NOT_SELECTED"
                  ? "Name a profile id or a strategy reference to load its governed expectancy profile."
                  : "Research has recorded no approved expectancy profile for that identity."}
              </p>
              <code className="research-empty__reason">
                {asText(expectancy.data?.reason) ?? "NO_EVIDENCE"}
              </code>
            </div>
          )}
        </EvidenceGate>
      </Section>
    </div>
  );
}
