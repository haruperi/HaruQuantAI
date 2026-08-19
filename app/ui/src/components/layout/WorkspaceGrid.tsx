'use client';

/**
 * Workspace content router (FEAT-UI-16).
 *
 * Decides what the workspace area shows for the active workspace: the template
 * picker while the workspace is pending its template choice, the explicit
 * empty-state prompt when it has no widgets, or the docking layout host that
 * renders every registered widget with fluid splitters and docking.
 */
import React from 'react';

import { useWorkspaceStore, TemplatePicker, WorkspaceEmptyState } from '../../widgets/workspaces';
import { DockingWorkspace } from './DockingWorkspace';

export const WorkspaceGrid: React.FC = () => {
  const workspaces = useWorkspaceStore((state) => state.workspaces);
  const activeWorkspaceId = useWorkspaceStore((state) => state.activeWorkspaceId);

  // eslint-disable-next-line eqeqeq -- workspace id is number; caller may pass string
  const currentWorkspace = workspaces.find((w) => w.id == activeWorkspaceId) || workspaces[0];

  // A workspace still pending its template choice renders the picker as its
  // whole content instead of a layout (FR-UI-195).
  if (currentWorkspace.templateChoicePending) {
    return <TemplatePicker />;
  }

  if (currentWorkspace.widgets.length === 0) {
    return (
      <main className="workspace-container workspace-empty-container">
        <WorkspaceEmptyState />
      </main>
    );
  }

  // A fresh docking host per workspace keeps serialized layouts from leaking
  // across workspaces on switch.
  return <DockingWorkspace key={currentWorkspace.id} workspace={currentWorkspace} />;
};
