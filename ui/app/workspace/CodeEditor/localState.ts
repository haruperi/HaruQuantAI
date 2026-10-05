/** Owner-local prototype state. Shared published resources are accessed through the host. */
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { ownerViewStorage, mergeViewState, previewResources, connectPreviewDocument } from '../../host/resourceClient';
import { useAppStore as useShellStore } from '../../host/store';
import type { ExtensionFile } from './documents';
interface LocalState { extensionFiles: ExtensionFile[];
activeFileId: string;
saveFile: (id: string) => void;
setCompileOutput: (output: string) => void;
openFile: (id: string) => void;
deleteExtensionFile: (id: string) => void;
openFileIds: string[];
setActiveFile: (id: string) => void;
closeFile: (id: string) => void;
updateFileContent: (id: string, content: string) => void;
compileOutput: string;
addExtensionFile: (file: ExtensionFile) => void; reset: () => void; }

const extensionFiles: ExtensionFile[] = JSON.parse("[{\"id\":\"ext-1\",\"name\":\"KeltnerChannel.java\",\"category\":\"Indicators\",\"language\":\"java\",\"content\":\"package HaruQuantAI.Indicators;\\n\\nimport haruquantai.lib.core.*;\\nimport haruquantai.lib.indicators.*;\\n\\n/**\\n * Keltner Channel Volatility Envelope Indicator\\n * Standard StrategyQuant X extension definition.\\n */\\npublic class KeltnerChannel extends Indicator {\\n    @Parameter(name = \\\"Period\\\", defaultValue = \\\"20\\\", min = 2, max = 200)\\n    public int period = 20;\\n\\n    @Parameter(name = \\\"Multiplier\\\", defaultValue = \\\"2.0\\\", min = 0.5, max = 10.0)\\n    public double multiplier = 2.0;\\n\\n    @Output(name = \\\"UpperBand\\\")\\n    public DataSeries upper;\\n\\n    @Output(name = \\\"MiddleBand\\\")\\n    public DataSeries middle;\\n\\n    @Output(name = \\\"LowerBand\\\")\\n    public DataSeries lower;\\n\\n    @Override\\n    public void compute(int bar) {\\n        middle.set(bar, Indicators.EMA(chart.Close, period, bar));\\n        double atr = Indicators.ATR(chart, period, bar);\\n        upper.set(bar, middle.get(bar) + (multiplier * atr));\\n        lower.set(bar, middle.get(bar) - (multiplier * atr));\\n    }\\n}\"},{\"id\":\"ext-2\",\"name\":\"TrailingStopVolatility.java\",\"category\":\"Snippets\",\"language\":\"java\",\"content\":\"package HaruQuantAI.Snippets;\\n\\nimport haruquantai.lib.order.*;\\n\\npublic class TrailingStopVolatility {\\n    public static void applyTrailingStop(Order order, double currentPrice, double atrValue, double atrMultiplier) {\\n        if (order.isLong()) {\\n            double newStop = currentPrice - (atrValue * atrMultiplier);\\n            if (newStop > order.getStopLoss()) {\\n                order.setStopLoss(newStop);\\n            }\\n        } else if (order.isShort()) {\\n            double newStop = currentPrice + (atrValue * atrMultiplier);\\n            if (newStop < order.getStopLoss() || order.getStopLoss() == 0) {\\n                order.setStopLoss(newStop);\\n            }\\n        }\\n    }\\n}\"},{\"id\":\"ext-3\",\"name\":\"SuperTrendBlock.java\",\"category\":\"Blocks\",\"language\":\"java\",\"content\":\"package HaruQuantAI.Blocks;\\n\\nimport haruquantai.lib.buildingblocks.*;\\n\\n@BuildingBlock(name = \\\"SuperTrend Direction Filter\\\", category = \\\"Trend Filters\\\")\\npublic class SuperTrendBlock extends ConditionBlock {\\n    @Parameter(name = \\\"Period\\\", defaultValue = \\\"10\\\")\\n    public int period = 10;\\n\\n    @Parameter(name = \\\"Multiplier\\\", defaultValue = \\\"3.0\\\")\\n    public double multiplier = 3.0;\\n\\n    @Override\\n    public boolean evaluate(Chart chart, int bar) {\\n        double currentClose = chart.Close.get(bar);\\n        double supertrend = Indicators.SuperTrend(chart, period, multiplier, bar);\\n        return currentClose > supertrend;\\n    }\\n}\"},{\"id\":\"ext-4\",\"name\":\"UlcerIndexColumn.java\",\"category\":\"Columns\",\"language\":\"java\",\"content\":\"package HaruQuantAI.Columns;\\n\\nimport haruquantai.lib.databank.*;\\n\\npublic class UlcerIndexColumn extends DatabankColumn {\\n    public UlcerIndexColumn() {\\n        super(\\\"Ulcer Index\\\", \\\"UI\\\", \\\"Downside risk measurement of strategy equity drawdowns.\\\");\\n    }\\n\\n    @Override\\n    public double calculate(StrategyResult result) {\\n        double[] dd = result.getDrawdownSeries();\\n        if (dd == null || dd.length == 0) return 0.0;\\n        double sumSq = 0.0;\\n        for (double d : dd) {\\n            sumSq += (d * d);\\n        }\\n        return Math.sqrt(sumSq / dd.length);\\n    }\\n}\"},{\"id\":\"ext-5\",\"name\":\"WalkForwardEfficiency.java\",\"category\":\"CustomAnalysis\",\"language\":\"java\",\"content\":\"package HaruQuantAI.CustomAnalysis;\\n\\nimport haruquantai.lib.analysis.*;\\n\\npublic class WalkForwardEfficiency extends AnalysisPlugin {\\n    @Override\\n    public AnalysisResult analyze(StrategyResult isResult, StrategyResult oosResult) {\\n        double isAnnualized = isResult.getAnnualizedReturn();\\n        double oosAnnualized = oosResult.getAnnualizedReturn();\\n        double wfe = isAnnualized > 0 ? (oosAnnualized / isAnnualized) * 100.0 : 0.0;\\n        return new AnalysisResult(\\\"Walk-Forward Efficiency (%)\\\", wfe, wfe >= 50.0 ? Verdict.PASS : Verdict.FAIL);\\n    }\\n}\"},{\"id\":\"ext-6\",\"name\":\"EquityDriftHeatmap.java\",\"category\":\"ResultsPlugins\",\"language\":\"java\",\"content\":\"package HaruQuantAI.ResultsPlugins;\\n\\nimport haruquantai.lib.visualization.*;\\n\\npublic class EquityDriftHeatmap extends VisualResultTab {\\n    @Override\\n    public String getTabTitle() {\\n        return \\\"Equity Drift Analysis\\\";\\n    }\\n\\n    @Override\\n    public RenderableMatrix render(StrategyResult result) {\\n        return MatrixGenerator.generateRollingMonthlyReturns(result.getEquityCurve());\\n    }\\n}\"}]");
const useLocalState = create<LocalState>()(persist((set) => ({extensionFiles,
activeFileId: extensionFiles[0].id,
saveFile: id => set(s => ({
    extensionFiles: s.extensionFiles.map(f => f.id === id ? { ...f, dirty: false } : f),
  })),
setCompileOutput: compileOutput => set({ compileOutput }),
openFile: id => set(s => ({
    activeFileId: id,
    openFileIds: s.openFileIds.includes(id) ? s.openFileIds : [...s.openFileIds, id],
  })),
deleteExtensionFile: id => set(s => {
    const nextFiles = s.extensionFiles.filter(f => f.id !== id);
    const nextOpen = s.openFileIds.filter(fId => fId !== id);
    return {
      extensionFiles: nextFiles,
      openFileIds: nextOpen,
      activeFileId: s.activeFileId === id ? (nextOpen[0] || nextFiles[0]?.id || '') : s.activeFileId,
    };
  }),
openFileIds: [extensionFiles[0].id],
setActiveFile: activeFileId => set(s => ({
    activeFileId,
    openFileIds: s.openFileIds.includes(activeFileId) ? s.openFileIds : [...s.openFileIds, activeFileId],
  })),
closeFile: id => set(s => {
    const nextOpen = s.openFileIds.filter(fId => fId !== id);
    const nextActive = s.activeFileId === id ? (nextOpen[nextOpen.length - 1] || '') : s.activeFileId;
    return { openFileIds: nextOpen, activeFileId: nextActive };
  }),
updateFileContent: (id, content) => set(s => ({
    extensionFiles: s.extensionFiles.map(f => f.id === id ? { ...f, content, dirty: true } : f),
  })),
compileOutput: '[info] Compiler ready. Select an extension and click Compile to run AST validation.',
addExtensionFile: file => set(s => ({
    extensionFiles: [...s.extensionFiles, file],
    activeFileId: file.id,
    openFileIds: [...s.openFileIds, file.id],
  })), reset: () => set({extensionFiles,
activeFileId: extensionFiles[0].id,
openFileIds: [extensionFiles[0].id],
compileOutput: '[info] Compiler ready. Select an extension and click Compile to run AST validation.'})}), {name: 'workspace.code_editor.view.v1', version: 1, storage:createJSONStorage(() => { if (typeof localStorage === 'undefined') throw new Error('Local view storage unavailable'); return ownerViewStorage; }), merge:mergeViewState}));

type CombinedState = ReturnType<typeof useShellStore.getState> & LocalState;
function useCombinedState<T = CombinedState>(selector: (state: CombinedState) => T = state => state as unknown as T): T {
 const shell=useShellStore(); const local=useLocalState(); return selector({...shell,...local});
}
export const useAppStore=Object.assign(useCombinedState, {getState: (): CombinedState => ({...useShellStore.getState(),...useLocalState.getState()}), setState: useLocalState.setState, subscribe: useLocalState.subscribe, persist:useLocalState.persist});
