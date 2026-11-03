package SQ.Blocks.Indicators.VolumeProfile;

import SQ.Internal.ConditionBlock;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.tradinglib.*;

@BuildingBlock(name = "(VP08) High Delta (Bull Dominance)", display = "HighDelta(@Chart@#SessionType#,#MinDelta#)", returnType = ReturnTypes.Boolean)
@Help("Session delta (bull volume minus bear volume) exceeds a minimum threshold. Positive delta confirms aggressive buying  --  order flow supports bullish setups.")
@OppositeBlock("VPHighNegDelta")
@ForEngine("MT4,MT5,TS,MC,NT")
public class VPHighDelta extends ConditionBlock {

    @Parameter
    public ChartData Chart;

    @Parameter(defaultValue = "Current", showIfDefault = false)
    @Editor(type = Editors.SelectionSymbols)
    public String Symbol;

    @Parameter(name = "Min Delta", defaultValue = "100", minValue = 1, maxValue = 100000, step = 10)
    @Help("Minimum positive delta (bull volume - bear volume) to trigger signal")
    public int MinDelta;

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
        VolumeProfile indicator = Strategy.Indicators.VolumeProfile(Chart, SessionType, ProfileRows, 2, 3, ValueAreaPct,
                0, 0, 5, 20, 40, false, false, 6.0, 2, 1, 2.0, 50, 1.5, 14, true, false, 20, true, true, true, true, false, false);

        double delta = indicator.Delta.getRounded(Shift);

        return delta > MinDelta;
    }

}
