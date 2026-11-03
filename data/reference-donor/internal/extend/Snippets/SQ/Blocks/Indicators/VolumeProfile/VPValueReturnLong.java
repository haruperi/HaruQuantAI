package SQ.Blocks.Indicators.VolumeProfile;

import SQ.Internal.ConditionBlock;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.tradinglib.*;

@BuildingBlock(name = "(VP12L) Value Return Long (80% Rule)", display = "ValueReturnLong(@Chart@#MinimumDeviation#)", returnType = ReturnTypes.Boolean)
@Help("After leaving value below VAL, price re-enters the value area -- the breakout failed. Based on the classic 80% Rule: once price returns into value, it tends to rotate through to the opposite edge. Long signal targeting PPOC then PVAH.")
@OppositeBlock("VPValueReturnShort")
@ForEngine("MT4,MT5,TS,MC,NT")
public class VPValueReturnLong extends ConditionBlock {

    @Parameter
    public ChartData Chart;

    @Parameter(defaultValue = "Current", showIfDefault = false)
    @Editor(type = Editors.SelectionSymbols)
    public String Symbol;

    @Parameter(name = "Minimum Deviation", defaultValue = "2", minValue = 0, maxValue = 100, step = 1)
    @Help("Minimum distance (in points) below VAL that the prior bar must have been to qualify as 'outside value'")
    public int MinimumDeviation;

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
        double eps = Strategy.convertPipsToRealPrice(Symbol, MinimumDeviation) / 10.0;

        VolumeProfile indicator = Strategy.Indicators.VolumeProfile(Chart, SessionType, ProfileRows, 2, 3, ValueAreaPct,
                0, 0, 5, 20, 40, false, false, 3.0, 3, 1, 2.0, 50, 1.5, 14, true, false, 20, true, true, true, true, false, false);

        double vah = indicator.VAH.getRounded(Shift);
        double val = indicator.VAL.getRounded(Shift);
        double close = Chart.Close(Shift);

        // Current bar must close inside value
        boolean nowInside = close >= val && close <= vah;
        if (!nowInside)
            return false;

        // Bar at +1 must have closed below VAL
        if (Chart.Close(Shift + 1) >= indicator.VAL.getRounded(Shift + 1) - eps)
            return false;

        return true;
    }

}
