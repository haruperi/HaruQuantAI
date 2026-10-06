import type { ExtensionFile } from '../../app/types';

export const extensionFiles: ExtensionFile[] = [
  {
    id: 'ext-1',
    name: 'KeltnerChannel.java',
    category: 'Indicators',
    language: 'java',
    content: `package HaruQuantAI.Indicators;

import haruquantai.lib.core.*;
import haruquantai.lib.indicators.*;

/**
 * Keltner Channel Volatility Envelope Indicator
 * Standard StrategyQuant X extension definition.
 */
public class KeltnerChannel extends Indicator {
    @Parameter(name = "Period", defaultValue = "20", min = 2, max = 200)
    public int period = 20;

    @Parameter(name = "Multiplier", defaultValue = "2.0", min = 0.5, max = 10.0)
    public double multiplier = 2.0;

    @Output(name = "UpperBand")
    public DataSeries upper;

    @Output(name = "MiddleBand")
    public DataSeries middle;

    @Output(name = "LowerBand")
    public DataSeries lower;

    @Override
    public void compute(int bar) {
        middle.set(bar, Indicators.EMA(chart.Close, period, bar));
        double atr = Indicators.ATR(chart, period, bar);
        upper.set(bar, middle.get(bar) + (multiplier * atr));
        lower.set(bar, middle.get(bar) - (multiplier * atr));
    }
}`,
  },
  {
    id: 'ext-2',
    name: 'TrailingStopVolatility.java',
    category: 'Snippets',
    language: 'java',
    content: `package HaruQuantAI.Snippets;

import haruquantai.lib.order.*;

public class TrailingStopVolatility {
    public static void applyTrailingStop(Order order, double currentPrice, double atrValue, double atrMultiplier) {
        if (order.isLong()) {
            double newStop = currentPrice - (atrValue * atrMultiplier);
            if (newStop > order.getStopLoss()) {
                order.setStopLoss(newStop);
            }
        } else if (order.isShort()) {
            double newStop = currentPrice + (atrValue * atrMultiplier);
            if (newStop < order.getStopLoss() || order.getStopLoss() == 0) {
                order.setStopLoss(newStop);
            }
        }
    }
}`,
  },
  {
    id: 'ext-3',
    name: 'SuperTrendBlock.java',
    category: 'Blocks',
    language: 'java',
    content: `package HaruQuantAI.Blocks;

import haruquantai.lib.buildingblocks.*;

@BuildingBlock(name = "SuperTrend Direction Filter", category = "Trend Filters")
public class SuperTrendBlock extends ConditionBlock {
    @Parameter(name = "Period", defaultValue = "10")
    public int period = 10;

    @Parameter(name = "Multiplier", defaultValue = "3.0")
    public double multiplier = 3.0;

    @Override
    public boolean evaluate(Chart chart, int bar) {
        double currentClose = chart.Close.get(bar);
        double supertrend = Indicators.SuperTrend(chart, period, multiplier, bar);
        return currentClose > supertrend;
    }
}`,
  },
  {
    id: 'ext-4',
    name: 'UlcerIndexColumn.java',
    category: 'Columns',
    language: 'java',
    content: `package HaruQuantAI.Columns;

import haruquantai.lib.databank.*;

public class UlcerIndexColumn extends DatabankColumn {
    public UlcerIndexColumn() {
        super("Ulcer Index", "UI", "Downside risk measurement of strategy equity drawdowns.");
    }

    @Override
    public double calculate(StrategyResult result) {
        double[] dd = result.getDrawdownSeries();
        if (dd == null || dd.length == 0) return 0.0;
        double sumSq = 0.0;
        for (double d : dd) {
            sumSq += (d * d);
        }
        return Math.sqrt(sumSq / dd.length);
    }
}`,
  },
  {
    id: 'ext-5',
    name: 'WalkForwardEfficiency.java',
    category: 'CustomAnalysis',
    language: 'java',
    content: `package HaruQuantAI.CustomAnalysis;

import haruquantai.lib.analysis.*;

public class WalkForwardEfficiency extends AnalysisPlugin {
    @Override
    public AnalysisResult analyze(StrategyResult isResult, StrategyResult oosResult) {
        double isAnnualized = isResult.getAnnualizedReturn();
        double oosAnnualized = oosResult.getAnnualizedReturn();
        double wfe = isAnnualized > 0 ? (oosAnnualized / isAnnualized) * 100.0 : 0.0;
        return new AnalysisResult("Walk-Forward Efficiency (%)", wfe, wfe >= 50.0 ? Verdict.PASS : Verdict.FAIL);
    }
}`,
  },
  {
    id: 'ext-6',
    name: 'EquityDriftHeatmap.java',
    category: 'ResultsPlugins',
    language: 'java',
    content: `package HaruQuantAI.ResultsPlugins;

import haruquantai.lib.visualization.*;

public class EquityDriftHeatmap extends VisualResultTab {
    @Override
    public String getTabTitle() {
        return "Equity Drift Analysis";
    }

    @Override
    public RenderableMatrix render(StrategyResult result) {
        return MatrixGenerator.generateRollingMonthlyReturns(result.getEquityCurve());
    }
}`,
  },
];
