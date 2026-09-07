'use client';

/**
 * Registry-backed widget rendering boundary (FEAT-UI-01/16).
 *
 * Shared by layout hosts so every surface that shows a widget renders the
 * exact same component for a given widget type. Extracted from the former
 * WorkspaceGrid widget switch.
 */
import React from 'react';

import {
  RegisteredWidgetContent,
  type Widget,
} from '../../widgets/workspaces';

export const WidgetContentHost: React.FC<{ widget: Widget }> = ({ widget }) => {
  return <RegisteredWidgetContent widget={widget} />;
};
