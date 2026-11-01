import { memo } from 'react';
import { ResultsChart } from '../../common/project';

export interface FrontierPoint {
  simulationIndex: number;
  weights: number[];
  riskX: number;
  returnY: number;
  selectionScore: number;
  isSelected: boolean;
}

export interface PortfolioComposerChartProps {
  modelType: string;
  selectionType: string;
  frontierPoints: FrontierPoint[];
  portfolioEquity: [number, number][];
  memberEquities?: Record<string, [number, number][]>;
}

export const ResultsPortfolioComposerChart = memo(function ResultsPortfolioComposerChart({
  modelType,
  selectionType,
  frontierPoints,
  portfolioEquity,
}: PortfolioComposerChartProps) {
  const selectedPoint = frontierPoints.find(p => p.isSelected);

  return (
    <div className="sqr-content pf-chart-view">
      <h4>Portfolio Composer Chart ({modelType} / {selectionType})</h4>
      {selectedPoint && (
        <p className="pf-selection-summary">
          Optimal Simulation #{selectedPoint.simulationIndex}: Score {selectedPoint.selectionScore.toFixed(3)}
        </p>
      )}
      <div className="pf-frontier-chart">
        <ResultsChart
          title={`Efficient Frontier (${frontierPoints.length} points)`}
          values={frontierPoints.map(p => p.returnY)}
          bars
        />
      </div>
      <div className="pf-composite-equity-chart">
        <ResultsChart
          title="Portfolio Composite Equity"
          values={portfolioEquity.map(p => p[1])}
        />
      </div>
    </div>
  );
});
