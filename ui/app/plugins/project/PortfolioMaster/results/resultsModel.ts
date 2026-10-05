export interface MockTrade {
    id: number;
    market: string;
    direction: 'long' | 'short';
    sample: 'in' | 'out';
    open: string;
    close: string;
    price: number;
    exit: number;
    profit: number;
    expired: boolean;
}
export interface ResultDocument {
    id: string;
    name: string;
    markets: string[];
    trades: MockTrade[];
    equity: number[];
    metrics: [
        string,
        string
    ][];
    chartData: boolean;
    stockpicker: boolean;
    portfolio: boolean;
}
/** Synthetic presentation document; no backend execution. */
export function demoResult(id: string, name: string): ResultDocument {
    const markets = ['Main backtest', 'EURUSD / H1', 'GBPUSD / H1'];
    return { id, name, markets, portfolio:!id.endsWith('3'), chartData: !id.endsWith('3'), stockpicker: id.endsWith('2'),
        metrics: resultSnapshot('both', 'full', 'Main backtest').metrics,
        equity: resultSnapshot('both', 'full', 'Main backtest').equity,
        trades: Array.from({ length: 24 }, (_, i) => ({ id: i + 1, market: markets[1 + i % 2], direction: i % 2 ? 'short' : 'long', sample: i < 16 ? 'in' : 'out', open: `2025-${String(1 + Math.floor(i / 2)).padStart(2, '0')}-${i % 2 ? '17' : '03'} 09:00`, close: `2025-${String(1 + Math.floor(i / 2)).padStart(2, '0')}-${i % 2 ? '18' : '04'} 16:00`, price: 1.0820 + i * .001, exit: 1.0840 + i * .001, profit: i === 23 ? 0 : [120, -40, 240, -120, 310, 310, -180, 390][i % 8], expired: i === 23 })) };
}
export function visibleTrades(result: ResultDocument, direction: string, sample: string, market: string, expired = false) { return result.trades.filter(t => (direction === 'both' || t.direction === direction) && (sample === 'full' || t.sample === sample) && (market === 'Main backtest' || t.market === market) && (expired || !t.expired)); }
export function csvTrades(trades: MockTrade[], decimalComma = false) {
    const separator = decimalComma ? ';' : ',';
    const escape = (v: string | number) => `"${String(v).replaceAll('"', '""')}"`;
    return [['ID', 'Market', 'Direction', 'Open time', 'Close time', 'Profit'], ...trades.map(t => [t.id, t.market, t.direction, t.open, t.close, decimalComma ? t.profit.toFixed(2).replace('.', ',') : t.profit.toFixed(2)])].map(row => row.map(escape).join(separator)).join('\r\n');
}
export function downloadText(name: string, text: string, type = 'text/plain') { const url = URL.createObjectURL(new Blob([text], { type })); const a = document.createElement('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
interface DisplaySnapshot {
    equity: number[];
    drawdown: number[];
    metrics: [
        string,
        string
    ][];
}
const displaySnapshots: Record<string, DisplaySnapshot> = {
    "both/full/Main backtest": {"equity": [10000, 10120, 10080, 10320, 10200, 10510, 10820, 10640, 11030, 11150, 11110, 11350, 11230, 11540, 11850, 11670, 12060, 12180, 12140, 12380, 12260, 12570, 12880, 12700], "drawdown": [0, -40, 0, -120, 0, 0, -180, 0, 0, -40, 0, -120, 0, 0, -180, 0, 0, -40, 0, -120, 0, 0, -180], "metrics": [["Total profit", "$ 2,700.00"], ["Profit factor", "3.65"], ["# of trades", "23"], ["Winning percentage", "60.87 %"], ["Drawdown", "$ 180.00"], ["Average trade", "$ 117.39"]]},
    "both/full/EURUSD / H1": {"equity": [10000, 10120, 10360, 10670, 10490, 10610, 10850, 11160, 10980, 11100, 11340, 11650, 11470], "drawdown": [0, 0, 0, -180, -60, 0, 0, -180, -60, 0, 0, -180], "metrics": [["Total profit", "$ 1,470.00"], ["Profit factor", "3.72"], ["# of trades", "12"], ["Winning percentage", "75.00 %"], ["Drawdown", "$ 180.00"], ["Average trade", "$ 122.50"]]},
    "both/full/GBPUSD / H1": {"equity": [10000, 9960, 9840, 10150, 10540, 10500, 10380, 10690, 11080, 11040, 10920, 11230], "drawdown": [-40, -160, 0, 0, -40, -160, 0, 0, -40, -160, 0], "metrics": [["Total profit", "$ 1,230.00"], ["Profit factor", "3.56"], ["# of trades", "11"], ["Winning percentage", "45.45 %"], ["Drawdown", "$ 160.00"], ["Average trade", "$ 111.82"]]},
    "both/in/Main backtest": {"equity": [10000, 10120, 10080, 10320, 10200, 10510, 10820, 10640, 11030, 11150, 11110, 11350, 11230, 11540, 11850, 11670, 12060], "drawdown": [0, -40, 0, -120, 0, 0, -180, 0, 0, -40, 0, -120, 0, 0, -180, 0], "metrics": [["Total profit", "$ 2,060.00"], ["Profit factor", "4.03"], ["# of trades", "16"], ["Winning percentage", "62.50 %"], ["Drawdown", "$ 180.00"], ["Average trade", "$ 128.75"]]},
    "both/in/EURUSD / H1": {"equity": [10000, 10120, 10360, 10670, 10490, 10610, 10850, 11160, 10980], "drawdown": [0, 0, 0, -180, -60, 0, 0, -180], "metrics": [["Total profit", "$ 980.00"], ["Profit factor", "3.72"], ["# of trades", "8"], ["Winning percentage", "75.00 %"], ["Drawdown", "$ 180.00"], ["Average trade", "$ 122.50"]]},
    "both/in/GBPUSD / H1": {"equity": [10000, 9960, 9840, 10150, 10540, 10500, 10380, 10690, 11080], "drawdown": [-40, -160, 0, 0, -40, -160, 0, 0], "metrics": [["Total profit", "$ 1,080.00"], ["Profit factor", "4.38"], ["# of trades", "8"], ["Winning percentage", "50.00 %"], ["Drawdown", "$ 160.00"], ["Average trade", "$ 135.00"]]},
    "both/out/Main backtest": {"equity": [10000, 10120, 10080, 10320, 10200, 10510, 10820, 10640], "drawdown": [0, -40, 0, -120, 0, 0, -180], "metrics": [["Total profit", "$ 640.00"], ["Profit factor", "2.88"], ["# of trades", "7"], ["Winning percentage", "57.14 %"], ["Drawdown", "$ 180.00"], ["Average trade", "$ 91.43"]]},
    "both/out/EURUSD / H1": {"equity": [10000, 10120, 10360, 10670, 10490], "drawdown": [0, 0, 0, -180], "metrics": [["Total profit", "$ 490.00"], ["Profit factor", "3.72"], ["# of trades", "4"], ["Winning percentage", "75.00 %"], ["Drawdown", "$ 180.00"], ["Average trade", "$ 122.50"]]},
    "both/out/GBPUSD / H1": {"equity": [10000, 9960, 9840, 10150], "drawdown": [-40, -160, 0], "metrics": [["Total profit", "$ 150.00"], ["Profit factor", "1.94"], ["# of trades", "3"], ["Winning percentage", "33.33 %"], ["Drawdown", "$ 160.00"], ["Average trade", "$ 50.00"]]},
    "long/full/Main backtest": {"equity": [10000, 10120, 10360, 10670, 10490, 10610, 10850, 11160, 10980, 11100, 11340, 11650, 11470], "drawdown": [0, 0, 0, -180, -60, 0, 0, -180, -60, 0, 0, -180], "metrics": [["Total profit", "$ 1,470.00"], ["Profit factor", "3.72"], ["# of trades", "12"], ["Winning percentage", "75.00 %"], ["Drawdown", "$ 180.00"], ["Average trade", "$ 122.50"]]},
    "long/full/EURUSD / H1": {"equity": [10000, 10120, 10360, 10670, 10490, 10610, 10850, 11160, 10980, 11100, 11340, 11650, 11470], "drawdown": [0, 0, 0, -180, -60, 0, 0, -180, -60, 0, 0, -180], "metrics": [["Total profit", "$ 1,470.00"], ["Profit factor", "3.72"], ["# of trades", "12"], ["Winning percentage", "75.00 %"], ["Drawdown", "$ 180.00"], ["Average trade", "$ 122.50"]]},
    "long/full/GBPUSD / H1": {"equity": [10000], "drawdown": [], "metrics": [["Total profit", "$ 0.00"], ["Profit factor", "—"], ["# of trades", "0"], ["Winning percentage", "—"], ["Drawdown", "$ 0.00"], ["Average trade", "—"]]},
    "long/in/Main backtest": {"equity": [10000, 10120, 10360, 10670, 10490, 10610, 10850, 11160, 10980], "drawdown": [0, 0, 0, -180, -60, 0, 0, -180], "metrics": [["Total profit", "$ 980.00"], ["Profit factor", "3.72"], ["# of trades", "8"], ["Winning percentage", "75.00 %"], ["Drawdown", "$ 180.00"], ["Average trade", "$ 122.50"]]},
    "long/in/EURUSD / H1": {"equity": [10000, 10120, 10360, 10670, 10490, 10610, 10850, 11160, 10980], "drawdown": [0, 0, 0, -180, -60, 0, 0, -180], "metrics": [["Total profit", "$ 980.00"], ["Profit factor", "3.72"], ["# of trades", "8"], ["Winning percentage", "75.00 %"], ["Drawdown", "$ 180.00"], ["Average trade", "$ 122.50"]]},
    "long/in/GBPUSD / H1": {"equity": [10000], "drawdown": [], "metrics": [["Total profit", "$ 0.00"], ["Profit factor", "—"], ["# of trades", "0"], ["Winning percentage", "—"], ["Drawdown", "$ 0.00"], ["Average trade", "—"]]},
    "long/out/Main backtest": {"equity": [10000, 10120, 10360, 10670, 10490], "drawdown": [0, 0, 0, -180], "metrics": [["Total profit", "$ 490.00"], ["Profit factor", "3.72"], ["# of trades", "4"], ["Winning percentage", "75.00 %"], ["Drawdown", "$ 180.00"], ["Average trade", "$ 122.50"]]},
    "long/out/EURUSD / H1": {"equity": [10000, 10120, 10360, 10670, 10490], "drawdown": [0, 0, 0, -180], "metrics": [["Total profit", "$ 490.00"], ["Profit factor", "3.72"], ["# of trades", "4"], ["Winning percentage", "75.00 %"], ["Drawdown", "$ 180.00"], ["Average trade", "$ 122.50"]]},
    "long/out/GBPUSD / H1": {"equity": [10000], "drawdown": [], "metrics": [["Total profit", "$ 0.00"], ["Profit factor", "—"], ["# of trades", "0"], ["Winning percentage", "—"], ["Drawdown", "$ 0.00"], ["Average trade", "—"]]},
    "short/full/Main backtest": {"equity": [10000, 9960, 9840, 10150, 10540, 10500, 10380, 10690, 11080, 11040, 10920, 11230], "drawdown": [-40, -160, 0, 0, -40, -160, 0, 0, -40, -160, 0], "metrics": [["Total profit", "$ 1,230.00"], ["Profit factor", "3.56"], ["# of trades", "11"], ["Winning percentage", "45.45 %"], ["Drawdown", "$ 160.00"], ["Average trade", "$ 111.82"]]},
    "short/full/EURUSD / H1": {"equity": [10000], "drawdown": [], "metrics": [["Total profit", "$ 0.00"], ["Profit factor", "—"], ["# of trades", "0"], ["Winning percentage", "—"], ["Drawdown", "$ 0.00"], ["Average trade", "—"]]},
    "short/full/GBPUSD / H1": {"equity": [10000, 9960, 9840, 10150, 10540, 10500, 10380, 10690, 11080, 11040, 10920, 11230], "drawdown": [-40, -160, 0, 0, -40, -160, 0, 0, -40, -160, 0], "metrics": [["Total profit", "$ 1,230.00"], ["Profit factor", "3.56"], ["# of trades", "11"], ["Winning percentage", "45.45 %"], ["Drawdown", "$ 160.00"], ["Average trade", "$ 111.82"]]},
    "short/in/Main backtest": {"equity": [10000, 9960, 9840, 10150, 10540, 10500, 10380, 10690, 11080], "drawdown": [-40, -160, 0, 0, -40, -160, 0, 0], "metrics": [["Total profit", "$ 1,080.00"], ["Profit factor", "4.38"], ["# of trades", "8"], ["Winning percentage", "50.00 %"], ["Drawdown", "$ 160.00"], ["Average trade", "$ 135.00"]]},
    "short/in/EURUSD / H1": {"equity": [10000], "drawdown": [], "metrics": [["Total profit", "$ 0.00"], ["Profit factor", "—"], ["# of trades", "0"], ["Winning percentage", "—"], ["Drawdown", "$ 0.00"], ["Average trade", "—"]]},
    "short/in/GBPUSD / H1": {"equity": [10000, 9960, 9840, 10150, 10540, 10500, 10380, 10690, 11080], "drawdown": [-40, -160, 0, 0, -40, -160, 0, 0], "metrics": [["Total profit", "$ 1,080.00"], ["Profit factor", "4.38"], ["# of trades", "8"], ["Winning percentage", "50.00 %"], ["Drawdown", "$ 160.00"], ["Average trade", "$ 135.00"]]},
    "short/out/Main backtest": {"equity": [10000, 9960, 9840, 10150], "drawdown": [-40, -160, 0], "metrics": [["Total profit", "$ 150.00"], ["Profit factor", "1.94"], ["# of trades", "3"], ["Winning percentage", "33.33 %"], ["Drawdown", "$ 160.00"], ["Average trade", "$ 50.00"]]},
    "short/out/EURUSD / H1": {"equity": [10000], "drawdown": [], "metrics": [["Total profit", "$ 0.00"], ["Profit factor", "—"], ["# of trades", "0"], ["Winning percentage", "—"], ["Drawdown", "$ 0.00"], ["Average trade", "—"]]},
    "short/out/GBPUSD / H1": {"equity": [10000, 9960, 9840, 10150], "drawdown": [-40, -160, 0], "metrics": [["Total profit", "$ 150.00"], ["Profit factor", "1.94"], ["# of trades", "3"], ["Winning percentage", "33.33 %"], ["Drawdown", "$ 160.00"], ["Average trade", "$ 50.00"]]}
};
export function resultSnapshot(direction: string, sample: string, market: string): DisplaySnapshot { return displaySnapshots[`${direction}/${sample}/${market}`] ?? displaySnapshots["both/full/Main backtest"]; }
