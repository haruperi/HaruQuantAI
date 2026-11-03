package SQ.Blocks.Indicators.VolumeProfile;

import SQ.Internal.ConditionBlock;
import SQ.Blocks.Indicators.AnchoredVWAP.AnchoredVWAP;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.tradinglib.*;

@BuildingBlock(name = "(VP28) VWAP Cross Down", display = "VWAPCrossDown(@Chart@#SessionType#)", returnType = ReturnTypes.Boolean, mainIndicator = "AnchoredVWAP")
@Help("Price crosses below the Anchored VWAP — current close is below VWAP while previous close was at or above. Momentum shift signal, often used for intraday reversal entries when price loses the volume-weighted mean.")
@OppositeBlock("VPVWAPCrossUp")
@ForEngine("MT4,MT5,TS,MC,NT")
public class VPVWAPCrossDown extends ConditionBlock {

    @Parameter
    public ChartData Chart;

    @Parameter(defaultValue = "Current", showIfDefault = false)
    @Editor(type = Editors.SelectionSymbols)
    public String Symbol;

    @Parameter(defaultValue = "1", name = "SessionType", minValue = 1, maxValue = 2, step = 1)
    @Help("VWAP anchor period: Daily/Weekly")
    @Editor(type = Editors.Selection, values = "Daily=1,Weekly=2")
    public int SessionType;

    // *****************************************************************************************************************************************************

    @Parameter(defaultValue = "1", minValue = 1, maxValue = 1)
    public int Shift;

    // ------------------------------------------------------------------------

    @Override
    protected void OnInit() throws BlockDefinitionException {
    }

    @Override
    public boolean OnBlockEvaluate() throws TradingException {
        AnchoredVWAP avwap = Strategy.Indicators.AnchoredVWAP(Chart, SessionType, 1.0);

        double close = Chart.Close(Shift);
        double prevClose = Chart.Close(Shift + 1);
        double vwap = avwap.VWAP.getRounded(Shift);
        double prevVwap = avwap.VWAP.getRounded(Shift + 1);

        return close < vwap && prevClose >= prevVwap;
    }

}
