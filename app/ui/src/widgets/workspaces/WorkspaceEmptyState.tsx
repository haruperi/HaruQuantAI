'use client';

/**
 * Explicit empty-workspace prompt (FEAT-UI-01, FR-UI-026/197).
 *
 * Rendered by `WorkspaceGrid` when the active workspace has no widgets - for
 * example right after applying the Blank template - so an empty workspace
 * presents as an intentional state with a next step, matching the CME Group
 * Simulator's "Your workspace is empty" screen.
 */
import React from 'react';

export const WorkspaceEmptyState: React.FC = () => (
  <div className="workspace-empty-state">
    <h3>Your workspace is empty</h3>
    <p>Add a new widget from the menu on the left to get started!</p>
  </div>
);
