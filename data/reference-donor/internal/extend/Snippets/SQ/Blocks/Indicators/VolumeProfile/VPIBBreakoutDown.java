package SQ.Blocks.Indicators.VolumeProfile;

import SQ.Internal.ConditionBlock;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.tradinglib.*;

@BuildingBlock(name = "(VP19) IB Breakout Down", display = "IBBreakoutDown(@Chart@#SessionType#,#IBMinutes#)", returnType = ReturnTypes.Boolean)
@Help("Price is below the Initial Balance Low (IBL). One of the most powerful intraday VP setups  --  price leaving the IB range downward signals directional conviction and often leads to a full-range extension to the downside.")
@OppositeBlock("VPIBBreakoutUp")
@ForEngine("MT4,MT5,TS,MC,NT")
public class VPIBBreakoutDown extends ConditionBlock {

    @Parameter
    public ChartData Chart;

    @Parameter(defaultValue = "Current", showIfDefault = false)
    @Editor(type = Editors.SelectionSymbols)
    public String Symbol;

    @Parameter(name = "IB Minutes", defaultValue = "60", minValue = 15, maxValue = 480, step = 15)
    @Help("Initial Balance period in minutes from session open (e.g. 60 = first hour)")
    public int IBMinutes;

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
                IBMinutes, 0, 5, 20, 40, false, false, 6.0, 2, 1, 2.0, 50, 1.5, 14, true, false, 20, true, true, true, true, false, false);

        double close = Chart.Close(Shift);
        double ibl = indicator.IBL.getRounded(Shift);

        return ibl > 0 && close < ibl;
    }

}
