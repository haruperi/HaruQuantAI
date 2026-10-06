/**
 * Fixtures for the Builder Results tab parity (FEAT-UI-BUILDER_RESULTS_TAB).
 *
 * Donor evidence: retained target UI; current donor equivalence unverified. Tab registry positions come from
 * the ResultsTab plugin registrations; strings come from the RESULTS app
 * templates and language constants. Backend-driven option lists (sample
 * percentage items, MM types, demo custom-analysis tabs) ship as fixtures.
 */
/** Info line shown above the tab strip when nothing is selected. */
export const NO_RESULT_CHOSEN = 'No result chosen - Double-click on result on databank to see the details';
export type ResultTabId = 'overview' | 'spOverview' | 'tradeList' | 'equityChart' | 'tradeAnalysis' | 'profileChart' | 'strategyConfig' | 'sourceCode';
export interface ResultTabDef {
    id: string;
    title: string;
    position: number;
}
/** Built-in tabs visible while no result is chosen (registry position order). */
export const builtInResultTabs: ResultTabDef[] = [
    { id: 'overview', title: 'Overview', position: 10 },
    { id: 'spOverview', title: 'SP overview', position: 11 },
    { id: 'tradeList', title: 'List of trades', position: 20 },
    { id: 'equityChart', title: 'Equity chart', position: 30 },
    { id: 'tradeAnalysis', title: 'Trade analysis', position: 40 },
    { id: 'profileChart', title: 'Profile chart', position: 55 },
    { id: 'strategyConfig', title: 'Strategy config', position: 80 },
    { id: 'sourceCode', title: 'Source Code', position: 100 },
];
/**
 * Tabs registered by the donor but hidden until a result exists
 * (noResultItems in the results state config). Kept for documentation and
 * tests; visibility is selected from local fixture capabilities.
 */
export const hiddenUntilResultTabs: {
    id: string;
    title: string;
    position: number;
}[] = [
    { id: 'correlation', title: 'Portfolio correlation', position: 70 },
    { id: 'monteCarloTests', title: 'Monte Carlo tests', position: 60 },
    { id: 'stockpicker', title: 'Stockpicker log', position: 99 },
    { id: 'tradesOnChart', title: 'Trades on chart', position: 50 },
];
/** Custom analysis tabs shipped with the reference install (user plugins). */
export const defaultCustomAnalysisTabs: string[] = ['Prop Monte Carlo', 'Prop analytics'];
/** Menu items on custom analysis tabs (CustomResultsPluginAction registry). */
export const customAnalysisActions: {
    title: 'Rename' | 'Delete';
    position: number;
}[] = [
    { title: 'Rename', position: 10 },
    { title: 'Delete', position: 50 },
];
export type Direction = 'both' | 'long' | 'short';
export type SampleType = 'full' | 'in' | 'out';
export const directionOptions: {
    value: Direction;
    label: string;
}[] = [
    { value: 'both', label: 'L+S' },
    { value: 'long', label: 'Lng' },
    { value: 'short', label: 'Shr' },
];
/** Sample dropdown menu items (backend-driven in the donor; demo fixture). */
export const sampleListIn: string[] = ['IS 67%'];
export const sampleListOut: string[] = ['OOS 33%'];
/** Overview template selector options (backend init data; single evidenced item). */
export const overviewTemplates: {
    value: string;
    label: string;
}[] = [
    { value: 'SQDefault', label: 'SQ Default' },
];
/** List of trades saved views (ResultsTradelistViews; demo fixture). */
export const tradeListViews: {
    value: string;
    label: string;
}[] = [
    { value: 'Default', label: 'Default' },
];
/** Source code generator names as spelled in the donor template. */
export const sourceCodeGenerators: string[] = [
    'Pseudo Code(*.TXT)',
    'Expert Advisor for MetaTrader4 (*.MQ4)',
    'Expert Advisor for MetaTrader5 (*.MQ5)',
    'EasyLanguage for Tradestation / MultiCharts (*.el)',
    'Java (JForex)',
    'XML',
];
/** Money-management select for source code export (backend-driven; fixture). */
export const sourceCodeMmTypes: {
    value: string;
    label: string;
}[] = [
    { value: 'asInStrategy', label: 'As in strategy' },
    { value: 'notUsed', label: 'Not used' },
];
/** Benchmark normalization options (donor language strings). */
export const benchmarkNormalizations: {
    value: string;
    label: string;
}[] = [
    { value: 'off', label: 'off' },
    { value: 'drawdown', label: 'normalize by $ drawdown' },
    { value: 'drawdownPct', label: 'normalize by % drawdown' },
    { value: 'moneyManagement', label: 'normalize by money management' },
    { value: 'exposure', label: 'normalize by exposure' },
];
export interface EquityChartFilter {
    xaxis: 'trade' | 'time';
    drawdown: number;
    volume: string;
    dailychart: boolean;
    volatility: boolean;
    trendline: boolean;
    equity: string;
    stagnation: string | number;
    stagnationV2: string | number;
    points: string;
    crosshair: boolean;
    benchmarkOn: boolean;
    benchmarkSymbol: string;
    benchmarkNormalization: string;
}
export const equityChartDefaults: EquityChartFilter = {
    xaxis: 'trade',
    drawdown: 10,
    volume: '5',
    dailychart: false,
    volatility: false,
    trendline: false,
    equity: 'off',
    stagnation: 'full',
    stagnationV2: 0,
    points: 'all',
    crosshair: false,
    benchmarkOn: false,
    benchmarkSymbol: 'EURUSD',
    benchmarkNormalization: 'off',
};
/** Source code parameter-variable settings (variablesSettings directive). */
export interface SourceCodeParamsConfig {
    parametrizeType: number;
    periodParams: boolean;
    constantsParams: boolean;
    shiftParams: boolean;
    otherParams: boolean;
    entryParams: boolean;
    entryLogic: boolean;
    exitParamsUsed: boolean;
    exitParamsUnused: boolean;
    booleanParams: boolean;
    symmetricVariables: boolean;
}
export const sourceCodeParamsDefaults: SourceCodeParamsConfig = {
    parametrizeType: 0,
    periodParams: true,
    constantsParams: true,
    shiftParams: false,
    otherParams: true,
    entryParams: true,
    entryLogic: true,
    exitParamsUsed: true,
    exitParamsUnused: false,
    booleanParams: false,
    symmetricVariables: true,
};
/** Generator descriptions (donor language file, paraphrase-free UI strings). */
export const sourceCodeDescriptions: Record<string, string> = {
    'Pseudo Code(*.TXT)': 'Saves strategy as human readable pseudo code, ready for manual trading',
    'Expert Advisor for MetaTrader4 (*.MQ4)': 'Saves strategy as MetaTrader4 EA. You should save this file to <terminal>/MQL4/Experts directory',
    'Expert Advisor for MetaTrader5 (*.MQ5)': 'Saves strategy as MetaTrader5 EA. You should save this file to <terminal>/MQL5/Experts directory',
    'EasyLanguage for Tradestation / MultiCharts (*.el)': 'Saves Strategy EasyLanguage code.',
    'Java (JForex)': 'Saves strategy as JForex code',
    XML: 'Saves Strategy XML code.',
};
/** Sorted strip: built-ins by position, custom analyses last (donor rule). */
export interface OrderedResultTab {
    id: string;
    title: string;
    position: number;
    isCustom?: boolean;
}
export function orderResultTabs(builtIns: ResultTabDef[], customTitles: string[]): OrderedResultTab[] {
    const custom = customTitles.map((title, i) => ({
        id: `custom:${title}`,
        title,
        position: 1000 + i,
        isCustom: true,
    }));
    return [...[...builtIns].sort((a, b) => a.position - b.position), ...custom];
}
