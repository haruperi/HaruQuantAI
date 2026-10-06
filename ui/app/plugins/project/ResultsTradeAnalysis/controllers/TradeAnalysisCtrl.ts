import { useState } from 'react';
import type { Direction, SampleType } from '../../ProjectWorkbench/results/resultsFixtures';

/** Existing report filters and open/close-time choice. */
export function useTradeAnalysis() {
    const [direction, setDirection] = useState<Direction>('both');
    const [sampleType, setSampleType] = useState<SampleType>('full');
    const [dataKey, setDataKey] = useState("Main backtest");
    const [period, setPeriod] = useState(1);
    return { direction, setDirection, sampleType, setSampleType, dataKey, setDataKey, period, setPeriod };
}
