package SQ.Blocks.Indicators.VolumeProfile;

import SQ.Internal.ConditionBlock;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.tradinglib.*;

@BuildingBlock(name = "(VP13L) Late Acceptance Failure Long", display = "LateAcceptFailLong(@Chart@#MinimumDeviation#)", returnType = ReturnTypes.Boolean)
@Help("Market attempted acceptance below value (multiple closes below VAL) but later fails and returns into value. The extended acceptance below was a trap -- fade back toward POC then opposite VA edge (PVAH). Stronger than a simple value return because multiple bars confirmed the attempted breakout.")
@OppositeBlock("VPLateAcceptanceFailureShort")
@ForEngine("MT4,MT5,TS,MC,NT")
public class VPLateAcceptanceFailureLong extends ConditionBlock {

    @Parameter
    public ChartData Chart;

    @Parameter(defaultValue = "Current", showIfDefault = false)
    @Editor(type = Editors.SelectionSymbols)
    public String Symbol;

    @Parameter(name = "Minimum Deviation", defaultValue = "1", minValue = 0, maxValue = 100, step = 1)
    @Help("Minimum distance (in points) below VAL for bars to qualify as outside value")
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

        // Current bar must close inside value (the "return")
        double close = Chart.Close(Shift);
        boolean nowInside = close >= indicator.VAL.getRounded(Shift) && close <= indicator.VAH.getRounded(Shift);
        if (!nowInside)
            return false;

        // Fixed 3-bar check: bars at +1, +2, +3 must all have closed below VAL
        if (Chart.Close(Shift + 1) >= indicator.VAL.getRounded(Shift + 1) - eps) return false;
        if (Chart.Close(Shift + 2) >= indicator.VAL.getRounded(Shift + 2) - eps) return false;
        if (Chart.Close(Shift + 3) >= indicator.VAL.getRounded(Shift + 3) - eps) return false;

        return true;
    }

}
