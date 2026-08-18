/**
 * News Workstation Page (FEAT-UI-29 / FR-UI-258).
 * Standalone workstation view hosting the live News widget.
 */

'use client';

import React from 'react';
import { ProtectedLayout } from '@/app/protected-layout';
import { NewsWidget } from '@/features/news';

export default function NewsPage(): React.JSX.Element {
  return (
    <ProtectedLayout>
      <div style={{ width: '100%', height: 'calc(100vh - 64px)', overflow: 'hidden' }}>
        <NewsWidget height="100%" />
      </div>
    </ProtectedLayout>
  );
}
