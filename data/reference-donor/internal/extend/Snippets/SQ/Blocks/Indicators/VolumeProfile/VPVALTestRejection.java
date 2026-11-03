package SQ.Blocks.Indicators.VolumeProfile;

import SQ.Internal.ConditionBlock;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.tradinglib.*;

@BuildingBlock(name = "(VP10) VAL Test Rejection (Long)", display = "VALTestRejection(@Chart@#MinimumWick#)", returnType = ReturnTypes.Boolean)
@Help("Price probes below prior VAL (low dips below PVAL) but closes back above PVAL -- responsive buyers defend the value edge. Classic long setup: enter long near VAL after rejection. Targets: PPOC then PVAH.")
@OppositeBlock("VPVAHTestRejection")
@ForEngine("MT4,MT5,TS,MC,NT")
public class VPVALTestRejection extends ConditionBlock {

    @Parameter
    public ChartData Chart;

    @Parameter(defaultValue = "Current", showIfDefault = false)
    @Editor(type = Editors.SelectionSymbols)
    public String Symbol;

    @Parameter(name = "Minimum Wick", defaultValue = "2", minValue = 0, maxValue = 100, step = 1)
    @Help("Minimum wick below VAL (in points) to qualify as a test")
    public int MinimumWick;

    @Parameter(name = "Minimum Rejection", defaultValue = "2", minValue = 0, maxValue = 100, step = 1)
    @Help("Minimum distance (in points) that the close must be above VAL to confirm rejection")
    public int MinimumRejection;

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
        double rejMin = Strategy.convertPipsToRealPrice(Symbol, MinimumRejection) / 10.0;

        VolumeProfile indicator = Strategy.Indicators.VolumeProfile(Chart, SessionType, ProfileRows, 2, 3, ValueAreaPct,
                0, 0, 5, 20, 40, false, false, 3.0, 3, 1, 2.0, 50, 1.5, 14, true, false, 20, true, true, true, true, false, false);

        double val = indicator.VAL.getRounded(Shift);
        double low = Chart.Low(Shift);
        double close = Chart.Close(Shift);

        // Low probes below VAL AND close rejects back above VAL
        return low < val - wickMin && close > val + rejMin;
    }

}
