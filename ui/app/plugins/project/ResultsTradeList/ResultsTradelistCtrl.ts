import { useState } from 'react';
import { visibleTrades, type ResultDocument } from '../ProjectWorkbench/results/resultsModel';
import type { Direction, SampleType } from '../ProjectWorkbench/results/resultsFixtures';

/** Existing trade filtering/sorting and export-dialog lifetime. */
export function useResultsTradelist(result: ResultDocument | null) {
    const [direction, setDirection] = useState<Direction>('both');
    const [sampleType, setSampleType] = useState<SampleType>('full');
    const [dataKey, setDataKey] = useState('Main backtest');
    const [expired, setExpired] = useState(false);
    const [ascending, setAscending] = useState(true);
    const [sort, setSort] = useState<'id' | 'profit'>('id');
    const [exportOpen, setExportOpen] = useState(false);
    const trades = result ? visibleTrades(result, direction, sampleType, dataKey, expired).sort((a, b) => (ascending ? 1 : -1) * (a[sort] - b[sort])) : [];
    return { direction, setDirection, sampleType, setSampleType, dataKey, setDataKey, expired, setExpired, ascending, setAscending, sort, setSort, exportOpen, setExportOpen, trades };
}
