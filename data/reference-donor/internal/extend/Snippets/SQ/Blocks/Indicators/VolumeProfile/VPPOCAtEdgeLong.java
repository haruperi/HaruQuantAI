package SQ.Blocks.Indicators.VolumeProfile;

import SQ.Internal.ConditionBlock;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.tradinglib.*;

@BuildingBlock(name = "(VPEL) POC At Edge Long (Imbalanced Up)", display = "POCAtEdgeLong(@Chart@#EdgePct#)", returnType = ReturnTypes.Boolean)
@Help("POC sits near the top of the value area (within EdgePct% of the VA range from VAH). When the most-traded price is at the top of value, the market is imbalanced upward -- the auction is 'one-sided' and likely to continue higher. Long regime filter.")
@OppositeBlock("VPPOCAtEdgeShort")
@ForEngine("MT4,MT5,TS,MC,NT")
public class VPPOCAtEdgeLong extends ConditionBlock {

    @Parameter
    public ChartData Chart;

    @Parameter(defaultValue = "Current", showIfDefault = false)
    @Editor(type = Editors.SelectionSymbols)
    public String Symbol;

    @Parameter(name = "Edge Pct", defaultValue = "20", minValue = 5, maxValue = 50, step = 5)
    @Help("POC must be within this percentage of the VA range from VAH. E.g., 20 means POC is in the top 20% of the VA.")
    public int EdgePct;

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

    @Override
    protected void OnInit() throws BlockDefinitionException {
    }

    @Override
    public boolean OnBlockEvaluate() throws TradingException {
        return _evaluateSignal();
    }

    private boolean _evaluateSignal() throws TradingException {
        VolumeProfile indicator = Strategy.Indicators.VolumeProfile(Chart, SessionType, ProfileRows, 2, 3, ValueAreaPct,
                0, 0, 5, 20, 40, false, false, 3.0, 3, 1, 2.0, 50, 1.5, 14, true, false, 20, true, true, true, true, false, false);

        double poc = indicator.POC.getRounded(Shift);
        double vah = indicator.VAH.getRounded(Shift);
        double val = indicator.VAL.getRounded(Shift);

        double vaRange = vah - val;
        if (vaRange <= 0)
            return false;

        // POC is within EdgePct% of VAH (top of value)
        double edgeThreshold = vaRange * EdgePct / 100.0;
        return poc >= vah - edgeThreshold;
    }

}
