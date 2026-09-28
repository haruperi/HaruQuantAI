/** Owner-local presentation/resource documents; no backend execution authority. */
export interface PortfolioMember {
  strategyId: string;
  weight: number;
  enabled: boolean;
  sector: string;
  multiplier?: number;
  color?: string;
  metrics?: {
    netProfit: number;
    maxDrawdown: number;
    profitFactor: number;
    sharpe: number;
  };
}
