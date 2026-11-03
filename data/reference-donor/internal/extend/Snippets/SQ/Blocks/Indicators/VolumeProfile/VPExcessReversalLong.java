package SQ.Blocks.Indicators.VolumeProfile;

import SQ.Internal.ConditionBlock;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.tradinglib.*;

@BuildingBlock(name = "(VP27L) Excess Reversal Long (Tail)", display = "ExcessReversalLong(@Chart@#MinimumWick#,#WickRatio#)", returnType = ReturnTypes.Boolean)
@Help("Strong rejection at the lower extreme: price trades below VAL (wick below) then closes back inside value with a long lower wick relative to body. This excess/tail indicates strong responsive buying. Long signal targeting PPOC then PVAH.")
@OppositeBlock("VPExcessReversalShort")
@ForEngine("MT4,MT5,TS,MC,NT")
public class VPExcessReversalLong extends ConditionBlock {

    @Parameter
    public ChartData Chart;

    @Parameter(defaultValue = "Current", showIfDefault = false)
    @Editor(type = Editors.SelectionSymbols)
    public String Symbol;

    @Parameter(name = "Minimum Wick", defaultValue = "2", minValue = 0, maxValue = 100, step = 1)
    @Help("Minimum wick below VAL (in points) to qualify as excess")
    public int MinimumWick;

    @Parameter(name = "Wick Ratio", defaultValue = "20", minValue = 10, maxValue = 100, step = 5)
    @Help("Minimum ratio of wick-to-body (x10, so 20 = 2.0x). The rejection wick must be this many times larger than the candle body to confirm excess.")
    public int WickRatio;

    // *****************************************************************************************************************************************************

    @Parameter(defaultValue = "1", name = "SessionType", minValue = 1, maxValue = 2, step = 1)
    @Help("Session selection: Previous/Actual Day/Week for profile calculation")
    @Editor(type = Editors.Selection, values = "Previous Day=1,Previous Week=2")
    public int SessionType;

    @Parameter(defaultValue = "50", name = "ProfileRows", minValue = 10, maxValue = 100, step = 10)
    @Help("Number of price levels (bins) in the profile")
    public int ProfileRows;

    @Parameter(defaultValue = "70", name = "ValueAreaPct", minValue = 65, maxValue = 75, step = 5)
    @Help("Percentage of total volume that defines the Value Area")
    public double ValueAreaPct;


    // *****************************************************************************************************************************************************

    @Parameter(defaultValue = "1", minValue = 1, maxValue = 1)
    public int Shift;

    // ------------------------------------------------------------------------

    @Override
    protected void OnInit() throws BlockDefinitionException {
    }

    @Override
    public boolean OnBlockEvaluate() throws TradingException {
        return _evaluateSignal();
    }

    private boolean _evaluateSignal() throws TradingException {
        double wickMin = Strategy.convertPipsToRealPrice(Symbol, MinimumWick) / 10.0;
        double wickRatioReal = WickRatio / 10.0;

        VolumeProfile indicator = Strategy.Indicators.VolumeProfile(Chart, SessionType, ProfileRows, 2, 3, ValueAreaPct,
                0, 0, 5, 20, 40, false, false, 3.0, 3, 1, 2.0, 50, 1.5, 14, true, false, 20, true, true, true, true, false, false);

        double val = indicator.VAL.getRounded(Shift);
        double vah = indicator.VAH.getRounded(Shift);

        double open = Chart.Open(Shift);
        double high = Chart.High(Shift);
        double low = Chart.Low(Shift);
        double close = Chart.Close(Shift);

        // Wick must reach below VAL
        if (low >= val - wickMin)
            return false;

        // Close must be back inside value
        if (close < val || close > vah)
            return false;

        // Check wick ratio: lower wick vs body
        double body = Math.abs(close - open);
        double lowerWick = Math.min(open, close) - low;
        double tickSize = Strategy.convertPipsToRealPrice(Symbol, 1) / 10.0;

        return lowerWick > wickRatioReal * Math.max(body, tickSize);
    }

}
