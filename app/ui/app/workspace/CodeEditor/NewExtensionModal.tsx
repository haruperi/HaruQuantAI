import React, { useState } from 'react';
import { Code2, FileCode, Layers, Sliders, Sparkles } from 'lucide-react';
import type { ExtensionFile } from '../../host/types';
import { Button, Field, Modal, Select, TextInput } from '../../components/ui';

interface NewExtensionModalProps {
  onClose: () => void;
  onAddFile: (file: ExtensionFile) => void;
}

export function NewExtensionModal({ onClose, onAddFile }: NewExtensionModalProps) {
  const [category, setCategory] = useState<ExtensionFile['category']>('Indicators');
  const [name, setName] = useState<string>('MyCustomIndicator.java');
  const [language, setLanguage] = useState<'java' | 'python'>('java');

  const templates: Record<ExtensionFile['category'], { java: string; python: string }> = {
    Indicators: {
      java: `package HaruQuantAI.Indicators;

import haruquantai.lib.core.*;
import haruquantai.lib.indicators.*;

public class MyCustomIndicator extends Indicator {
    @Parameter(name = "Period", defaultValue = "14", min = 2, max = 200)
    public int period = 14;

    @Output(name = "Value")
    public DataSeries value;

    @Override
    public void compute(int bar) {
        double close = chart.Close.get(bar);
        double sma = Indicators.SMA(chart.Close, period, bar);
        value.set(bar, (close - sma) / sma * 100.0);
    }
}`,
      python: `# HaruQuantAI Custom Indicator Extension
import numpy as np

class MyCustomIndicator:
    def __init__(self, period: int = 14):
        self.period = period

    def compute(self, close_series: np.ndarray) -> np.ndarray:
        weights = np.ones(self.period) / self.period
        sma = np.convolve(close_series, weights, mode='valid')
        return (close_series[-len(sma):] - sma) / sma * 100.0
`,
    },
    Snippets: {
      java: `package HaruQuantAI.Snippets;

import haruquantai.lib.order.*;

public class MyCustomSnippet {
    public static double calculateLotSize(double accountBalance, double riskPercent, double stopLossPips, double pointValue) {
        double riskAmount = accountBalance * (riskPercent / 100.0);
        double riskPerLot = stopLossPips * pointValue;
        return riskPerLot > 0 ? (riskAmount / riskPerLot) : 0.01;
    }
}`,
      python: `# HaruQuantAI Custom Snippet
def calculate_lot_size(account_balance: float, risk_percent: float, stop_loss_pips: float, point_value: float) -> float:
    risk_amount = account_balance * (risk_percent / 100.0)
    risk_per_lot = stop_loss_pips * point_value
    return round(risk_amount / risk_per_lot, 2) if risk_per_lot > 0 else 0.01
`,
    },
    Blocks: {
      java: `package HaruQuantAI.Blocks;

import haruquantai.lib.buildingblocks.*;

@BuildingBlock(name = "Custom Volatility Spike", category = "Volatility")
public class MyCustomBlock extends ConditionBlock {
    @Parameter(name = "Lookback", defaultValue = "20")
    public int lookback = 20;

    @Override
    public boolean evaluate(Chart chart, int bar) {
        double currentRange = chart.High.get(bar) - chart.Low.get(bar);
        double atr = Indicators.ATR(chart, lookback, bar);
        return currentRange > (atr * 2.0);
    }
}`,
      python: `# HaruQuantAI Custom Block
def evaluate_volatility_spike(high: float, low: float, atr: float, threshold_multiplier: float = 2.0) -> bool:
    bar_range = high - low
    return bar_range > (atr * threshold_multiplier)
`,
    },
    Columns: {
      java: `package HaruQuantAI.Columns;

import haruquantai.lib.databank.*;

public class MyCustomColumn extends DatabankColumn {
    public MyCustomColumn() {
        super("Custom Ratio", "CR", "Custom profit to Ulcer Index ratio.");
    }

    @Override
    public double calculate(StrategyResult result) {
        return result.getNetProfit() / Math.max(1.0, result.getMaxDrawdown());
    }
}`,
      python: `# HaruQuantAI Databank Column
def calculate_custom_ratio(net_profit: float, max_drawdown: float) -> float:
    return round(net_profit / max(1.0, max_drawdown), 2)
`,
    },
    CustomAnalysis: {
      java: `package HaruQuantAI.CustomAnalysis;

import haruquantai.lib.analysis.*;

public class MyCustomAnalysis extends AnalysisPlugin {
    @Override
    public AnalysisResult analyze(StrategyResult result) {
        double winRate = result.getWinRate();
        double profitFactor = result.getProfitFactor();
        Verdict verdict = (winRate >= 50.0 && profitFactor >= 1.3) ? Verdict.PASS : Verdict.FAIL;
        return new AnalysisResult("Quality Score", winRate * profitFactor, verdict);
    }
}`,
      python: `# HaruQuantAI Custom Analysis Plugin
def analyze_strategy(win_rate: float, profit_factor: float) -> dict:
    score = win_rate * profit_factor
    verdict = "PASS" if (win_rate >= 50.0 and profit_factor >= 1.3) else "FAIL"
    return {"metric": "Quality Score", "value": round(score, 2), "verdict": verdict}
`,
    },
    ResultsPlugins: {
      java: `package HaruQuantAI.ResultsPlugins;

import haruquantai.lib.visualization.*;

public class MyCustomResultsPlugin extends VisualResultTab {
    @Override
    public String getTabTitle() {
        return "Custom Drawdown Heatmap";
    }

    @Override
    public RenderableMatrix render(StrategyResult result) {
        return MatrixGenerator.generateDrawdownHeatmap(result.getDrawdownSeries());
    }
}`,
      python: `# HaruQuantAI Results Visualizer
def render_drawdown_heatmap(drawdown_series: list) -> dict:
    return {"type": "heatmap", "data": drawdown_series, "colormap": "viridis"}
`,
    },
  };

  const handleCategoryChange = (newCat: ExtensionFile['category']) => {
    setCategory(newCat);
    const ext = language === 'java' ? '.java' : '.py';
    setName(`Custom${newCat}${ext}`);
  };

  const handleLanguageChange = (newLang: 'java' | 'python') => {
    setLanguage(newLang);
    const base = name.replace(/\.(java|py)$/, '');
    setName(`${base}.${newLang === 'java' ? 'java' : 'py'}`);
  };

  const handleCreate = () => {
    const rawName = name.trim() || `Custom${category}.${language === 'java' ? 'java' : 'py'}`;
    const newFile: ExtensionFile = {
      id: `ext-${Date.now()}`,
      name: rawName,
      category,
      language,
      content: templates[category][language],
      dirty: false,
    };
    onAddFile(newFile);
    onClose();
  };

  return (
    <Modal title="Create New StrategyQuant X Extension" onClose={onClose} width={520}>
      <div className="flex flex-col gap-3">
        <Field label="Extension Category">
          <Select value={category} onChange={v => handleCategoryChange(v as any)}>
            <option value="Indicators">Indicators (Custom indicator with data series)</option>
            <option value="Snippets">Snippets (Helper methods and math formulas)</option>
            <option value="Blocks">Blocks (AlgoWizard building blocks & conditions)</option>
            <option value="Columns">Columns (Custom databank metric column)</option>
            <option value="CustomAnalysis">CustomAnalysis (Robustness and validation plugins)</option>
            <option value="ResultsPlugins">ResultsPlugins (Custom visual result views)</option>
          </Select>
        </Field>

        <Field label="Language">
          <Select value={language} onChange={v => handleLanguageChange(v as any)}>
            <option value="java">Java (StrategyQuant X standard extension runtime)</option>
            <option value="python">Python (Antigravity quantitative scripting bridge)</option>
          </Select>
        </Field>

        <Field label="File Name">
          <TextInput value={name} onChange={e => setName(e.target.value)} />
        </Field>

        <div className="text-[11px] text-gray-400 bg-gray-900 p-2.5 rounded border border-gray-700 flex items-center gap-2">
          <Sparkles size={14} className="text-cyan-400 shrink-0" />
          <span>
            A fully compliant starter template conforming to HaruQuantAI extension APIs will be created.
          </span>
        </div>

        <div className="flex justify-end gap-2 pt-2 border-t border-gray-700">
          <Button onClick={onClose}>Cancel</Button>
          <Button className="primary" onClick={handleCreate}>
            Create Extension
          </Button>
        </div>
      </div>
    </Modal>
  );
}
