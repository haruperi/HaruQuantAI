/**
 * FX Market Hours Workstation Page (FEAT-UI-30 / FR-UI-264).
 * Standalone workstation view hosting the live Market Hours widget.
 */

'use client';

import React from 'react';
import { ProtectedLayout } from '@/app/protected-layout';
import { MarketHoursWidget } from '@/features/market-hours';

export default function MarketHoursPage(): React.JSX.Element {
  return (
    <ProtectedLayout>
      <div style={{ width: '100%', height: 'calc(100vh - 64px)', overflow: 'hidden' }}>
        <MarketHoursWidget height="100%" />
      </div>
    </ProtectedLayout>
  );
}
