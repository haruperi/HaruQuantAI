import { TradingDashboard } from './TradingDashboard';

export function TradingWorkspace() {
  return (
    <div className="flex flex-col h-full overflow-y-auto p-6 space-y-6">
      <div className="border-b border-border pb-4">
        <h1 className="text-2xl font-bold text-text">Live Trading Operations</h1>
        <p className="text-sm text-text-muted">
          Real-time broker telemetry, order routing, positions monitoring, and panic safeguards.
        </p>
      </div>

      <TradingDashboard />
    </div>
  );
}

export default TradingWorkspace;
