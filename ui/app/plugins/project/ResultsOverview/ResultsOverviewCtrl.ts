import { useState } from 'react';
import { resultSnapshot } from '../ProjectWorkbench/results/resultsModel';
import type { Direction, SampleType } from '../ProjectWorkbench/results/resultsFixtures';

/** Current overview filter and mock-template selection state. */
export function useResultsOverview() {
    const [dataKey, setDataKey] = useState("Main backtest");
    const [direction, setDirection] = useState<Direction>('both');
    const [sampleType, setSampleType] = useState<SampleType>('full');
    const [template, setTemplate] = useState('SQDefault');
    const snapshot = resultSnapshot(direction, sampleType, dataKey);
    return { dataKey, setDataKey, direction, setDirection, sampleType, setSampleType, template, setTemplate, snapshot };
}
