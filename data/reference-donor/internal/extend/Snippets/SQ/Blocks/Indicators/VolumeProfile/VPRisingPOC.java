package SQ.Blocks.Indicators.VolumeProfile;

import SQ.Internal.ConditionBlock;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.tradinglib.*;

@BuildingBlock(name = "(VP21) Rising POC (Long Regime)", display = "RisingPOC(@Chart@#MinimumShift#)", returnType = ReturnTypes.Boolean)
@Help("POC migration upward: current session POC is higher than the prior session POC by at least MinimumShift pips. Lookback is auto-calculated from chart timeframe. Rising fair value suggests a bullish regime—prefer long setups on pullbacks to prior POC/value levels.")
@OppositeBlock("VPFallingPOC")
@ForEngine("MT4,MT5,TS,MC,NT")
public class VPRisingPOC extends ConditionBlock {

    @Parameter
    public ChartData Chart;

    @Parameter(defaultValue = "Current", showIfDefault = false)
    @Editor(type = Editors.SelectionSymbols)
    public String Symbol;



    @Parameter(name = "Minimum Shift", defaultValue = "5", minValue = 1, maxValue = 100, step = 1)
    @Help("Minimum POC increase (in pips) to qualify as a rising POC")
    public int MinimumShift;

    @Parameter(name = "LookbackBars", defaultValue = "48", minValue = 1, maxValue = 5000, step = 1)
    @Help("How many bars to look back for the prior session value. 0 = auto-calculate from chart timeframe.")
    public int LookbackBars;

    // *****************************************************************************************************************************************************

    @Parameter(defaultValue = "1", name = "SessionType", minValue = 1, maxValue = 2, step = 1)
    @Help("Session selection: Previous/Actual Day/Week for profile calculation")
    @Editor(type = Editors.Selection, values = "Previous Day=1,Previous Week=2")
    public int SessionType;

    @Parameter(defaultValue = "50", name = "ProfileRows", minValue = 10, maxValue = 500, step = 10)
    @Help("Number of price levels (bins) in the profile")
    public int ProfileRows;

    @Parameter(defaultValue = "70", name = "ValueAreaPct", minValue = 30, maxValue = 95, step = 5)
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
        // Use explicit LookbackBars if set, otherwise auto-calculate from chart timeframe
        int lookbackBars = LookbackBars;
        if (lookbackBars <= 0) {
            int barMinutes = (int)(TimeframeManager.getMillis(Chart.Timeframe) / 60000);
            int baseBars = (barMinutes > 0) ? 1440 / barMinutes : 48;
            int multiplier = (SessionType == 3 || SessionType == 7) ? 22 : (SessionType == 2 || SessionType == 6) ? 5 : 1;
            lookbackBars = baseBars * multiplier;
        }

        double minShift = Strategy.convertPipsToRealPrice(Symbol, MinimumShift);

        VolumeProfile indicator = Strategy.Indicators.VolumeProfile(Chart, SessionType, ProfileRows, 2, 3, ValueAreaPct,
                0, 0, 5, 20, 40, false, false, 6.0, 2, 1, 2.0, 50, 1.5, 14, true, false, 20, true, true, true, true, false, false);

        double currentPOC = indicator.POC.getRounded(Shift);
        double priorPOC = indicator.POC.getRounded(Shift + lookbackBars);

        // POC has risen by at least MinimumShift
        return currentPOC > priorPOC + minShift;
    }

}
