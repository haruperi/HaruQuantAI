import { useState } from 'react';
import type { usePreviewRun } from '../ProjectWorkbench/projectFixtures';

/** Existing local presentation state; the preview clock remains shared. */
export function useEnginePanel(run: ReturnType<typeof usePreviewRun>) {
  const [detail, setDetail] = useState<string | null>(null);
  const [sample, setSample] = useState('Full');
  return { detail, setDetail, sample, setSample, running: run.status === 'running' };
}
