package SQ.Blocks.Indicators.VolumeProfile;

import SQ.Internal.ConditionBlock;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.tradinglib.*;

@BuildingBlock(name = "(VP23) Value Shift Up (Bull Regime)", display = "ValueShiftUp(@Chart@#MinimumGap#)", returnType = ReturnTypes.Boolean)
@Help("Strong bullish regime: current session's VAL sits entirely above the prior session's VAH. The entire value area has shifted higher, indicating aggressive acceptance of higher prices. Prefer long setups—buy pullbacks into the new value area.")
@OppositeBlock("VPValueShiftDown")
@ForEngine("MT4,MT5,TS,MC,NT")
public class VPValueShiftUp extends ConditionBlock {

    @Parameter
    public ChartData Chart;

    @Parameter(defaultValue = "Current", showIfDefault = false)
    @Editor(type = Editors.SelectionSymbols)
    public String Symbol;



    @Parameter(name = "Minimum Gap", defaultValue = "0", minValue = 0, maxValue = 100, step = 1)
    @Help("Minimum gap (in pips) between current VAL and prior VAH to trigger the signal. Set to 0 for any overlap-free shift.")
    public int MinimumGap;

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

        double minGap = Strategy.convertPipsToRealPrice(Symbol, MinimumGap);

        VolumeProfile indicator = Strategy.Indicators.VolumeProfile(Chart, SessionType, ProfileRows, 2, 3, ValueAreaPct,
                0, 0, 5, 20, 40, false, false, 6.0, 2, 1, 2.0, 50, 1.5, 14, true, false, 20, true, true, true, true, false, false);

        // Current session values (most recent computed session)
        double currentVAL = indicator.VAL.getRounded(Shift);
        // Prior session values (look back far enough to be in the previous session)
        double priorVAH = indicator.VAH.getRounded(Shift + lookbackBars);

        // Current VAL sits above prior VAH (value shifted entirely higher)
        return currentVAL > priorVAH + minGap;
    }

}
