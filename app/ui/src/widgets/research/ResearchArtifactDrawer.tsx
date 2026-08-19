/**
 * Artifact drawer (FEAT-UI-28, plan §10.16).
 *
 * Lists the safe artifact references the server persisted for a run: relative
 * path, format, size, content hash, and audit event identity. The browser
 * never chooses an artifact root and never holds artifact bytes.
 */

"use client";

import type { ReactNode } from "react";

import type { ResearchRunDetail } from "@/clients";

import { Badge, EvidenceTable, KeyValues, Section } from "./evidence";
import { EvidenceGate } from "./ResearchRunStatus";
import { formatBytes, hashPrefix } from "./research-selectors";
import { useArtifacts } from "./use-research";

/** Props accepted by `ResearchArtifactDrawer`. */
export interface ResearchArtifactDrawerProps {
  detail: ResearchRunDetail;
}

/** Artifact references for one run. */
export function ResearchArtifactDrawer({
  detail,
}: ResearchArtifactDrawerProps): ReactNode {
  const artifacts = useArtifacts(detail.run_id);
  const items = artifacts.data?.artifacts ?? detail.artifacts;

  return (
    <div className="research-panel">
      <Section
        title="Artifacts"
        description="Persisted by the server under its own artifact root. Each reference carries a content hash and an audit event id."
      >
        <EvidenceGate
          loading={artifacts.loading}
          error={artifacts.error}
          reload={artifacts.reload}
          ready
          loadingLabel="Loading artifact references…"
        >
          <KeyValues
            columns={3}
            items={[
              ["Run", detail.run_id],
              ["Artifacts", String(items.length)],
              [
                "Root owner",
                <Badge key="o" tone="neutral">
                  {artifacts.data?.artifact_root_owner ?? "api"}
                </Badge>,
              ],
            ]}
          />
          <EvidenceTable
            columns={[
              "Artifact",
              "Kind",
              "Format",
              "Path",
              "Size",
              "SHA-256",
              "Audit event",
            ]}
            emptyLabel={
              detail.status === "completed"
                ? "This run persisted no artifacts. Artifact saving can be disabled per run."
                : "Artifacts appear once the run completes."
            }
            rows={items.map((artifact) => [
              <code key={artifact.artifact_id}>{artifact.artifact_id}</code>,
              artifact.kind,
              <Badge key={`${artifact.artifact_id}-f`} tone="neutral">
                {artifact.format}
              </Badge>,
              <span key={`${artifact.artifact_id}-p`} className="is-mono">
                {artifact.relative_path}
              </span>,
              formatBytes(artifact.size_bytes),
              <span
                key={`${artifact.artifact_id}-h`}
                className="is-mono"
                title={artifact.sha256}
              >
                {hashPrefix(artifact.sha256, 16)}
              </span>,
              <span key={`${artifact.artifact_id}-a`} className="is-mono">
                {artifact.audit_event_id}
              </span>,
            ])}
          />
          <p className="research-note">
            Paths are relative to the server-owned artifact root. The root itself
            is never sent to a browser, and this page never requests one.
          </p>
        </EvidenceGate>
      </Section>
    </div>
  );
}
