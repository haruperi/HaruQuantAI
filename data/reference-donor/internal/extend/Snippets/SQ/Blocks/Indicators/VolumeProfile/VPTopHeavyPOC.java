package SQ.Blocks.Indicators.VolumeProfile;

import SQ.Internal.ConditionBlock;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.tradinglib.*;

@BuildingBlock(name = "(VP12) Top-Heavy POC (Distribution)", display = "TopHeavyPOC(@Chart@#SessionType#,#ThresholdPct#)", returnType = ReturnTypes.Boolean)
@Help("POC sits in the upper portion of the profile range. POCPctUp < ThresholdPct means the POC is close to the top. Distribution/selling pressure  --  most volume occurred near the highs, suggesting institutional distribution. Bearish context.")
@OppositeBlock("VPBottomHeavyPOC")
@ForEngine("MT4,MT5,TS,MC,NT")
public class VPTopHeavyPOC extends ConditionBlock {

    @Parameter
    public ChartData Chart;

    @Parameter(defaultValue = "Current", showIfDefault = false)
    @Editor(type = Editors.SelectionSymbols)
    public String Symbol;

    @Parameter(name = "Threshold Pct", defaultValue = "30", minValue = 5, maxValue = 50, step = 5)
    @Help("POCPctUp must be below this percentage to qualify as top-heavy (e.g. 30 = POC is in the top 30% of the profile range)")
    public int ThresholdPct;

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

        double pocPctUp = indicator.POCPctUp.getRounded(Shift);

        // POCPctUp = percentage distance from POC to top of range
        // Small value = POC is near the top = top-heavy
        return pocPctUp < ThresholdPct && pocPctUp > 0;
    }

}
