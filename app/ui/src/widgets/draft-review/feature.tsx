"use client";

import React, { useMemo } from "react";

import { resolveDraftReviewConfig, type DraftReviewConfig } from "./config";
import type {
  ConsequentialAction,
  DraftDiffEntry,
  ValidationSummary,
} from "./contracts";
import { DraftReview } from "./DraftReview";
import { OverlayFoundation } from "./OverlayFoundation";

export interface DraftReviewFeatureProps {
  readonly isOpen?: boolean;
  readonly title?: string;
  readonly description?: string;
  readonly isDestructive?: boolean;
  readonly isDirty?: boolean;
  readonly diffs?: readonly DraftDiffEntry[];
  readonly validation?: ValidationSummary;
  readonly action?: ConsequentialAction;
  readonly currentAuthoritativeHash?: string;
  readonly currentAuthoritativeRevision?: number | string;
  readonly onConfirm?: () => void;
  readonly onCancel?: () => void;
  readonly onDiscardDraft?: () => void;
  readonly onClose?: () => void;
  readonly config?: Partial<DraftReviewConfig>;
  readonly asOverlay?: boolean;
}

export function DraftReviewFeature({
  isOpen = true,
  title = "Review Changes & Consequential Action",
  description,
  isDestructive = false,
  isDirty = false,
  diffs,
  validation,
  action,
  currentAuthoritativeHash,
  currentAuthoritativeRevision,
  onConfirm,
  onCancel,
  onDiscardDraft,
  onClose,
  config: configOverrides,
  asOverlay = true,
}: DraftReviewFeatureProps): React.JSX.Element | null {
  // Validate strict config
  useMemo(() => resolveDraftReviewConfig(configOverrides), [configOverrides]);

  const content = (
    <DraftReview
      title={title}
      diffs={diffs}
      validation={validation}
      action={action}
      currentAuthoritativeHash={currentAuthoritativeHash}
      currentAuthoritativeRevision={currentAuthoritativeRevision}
      onConfirm={onConfirm}
      onCancel={onCancel}
      onDiscardDraft={onDiscardDraft}
    />
  );

  if (!asOverlay) {
    return (
      <div
        className="draft-review-panel-host"
        style={{
          padding: "16px",
          height: "100%",
          overflowY: "auto",
          backgroundColor: "#161b22",
          color: "#e1e4ea",
        }}
      >
        {content}
      </div>
    );
  }

  return (
    <OverlayFoundation
      isOpen={isOpen}
      title={title}
      description={description}
      role={isDestructive ? "alertdialog" : "dialog"}
      isDestructive={isDestructive}
      isDirty={isDirty}
      onClose={onClose ?? onCancel ?? (() => {})}
    >
      {content}
    </OverlayFoundation>
  );
}
