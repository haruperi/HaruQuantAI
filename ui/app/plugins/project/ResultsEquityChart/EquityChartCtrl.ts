import { useState } from 'react';
import { resultSnapshot } from '../ProjectWorkbench/results/resultsModel';
import { equityChartDefaults, type Direction, type EquityChartFilter, type SampleType } from '../ProjectWorkbench/results/resultsFixtures';

/** Existing chart filters and refresh state; no market calculation. */
export function useEquityChart() {
    const [dataKey, setDataKey] = useState("Main backtest");
    const [direction, setDirection] = useState<Direction>('both');
    const [sampleType, setSampleType] = useState<SampleType>('full');
    const [filter, setFilter] = useState<EquityChartFilter>(equityChartDefaults);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const set = <K extends keyof EquityChartFilter>(key: K, value: EquityChartFilter[K]) => setFilter(f => ({ ...f, [key]: value }));
    const [revision, setRevision] = useState(0);
    const snapshot = resultSnapshot(direction, sampleType, dataKey);
    const xAxisIsTime = filter.xaxis === 'time';
    return { dataKey, setDataKey, direction, setDirection, sampleType, setSampleType, filter, set, settingsOpen, setSettingsOpen, revision, setRevision, snapshot, xAxisIsTime };
}
