package SQ.Blocks.Indicators.VolumeProfile;

import SQ.Blocks.Price.SessionOHLCCalculator;
import SQ.Internal.ConditionBlock;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.tradinglib.*;

@BuildingBlock(name = "(VPODL) Open Drive Long", display = "OpenDriveLong(@Chart@#MinimumMove#,#SessionStartHours#,#SessionStartMinutes#)", returnType = ReturnTypes.Boolean)
@Help("Market opens and drives aggressively upward without looking back. All of the first DriveBars consecutive bars after session open close higher than their opens (bullish candles) and the cumulative move exceeds MinimumMove pips. This is a high-conviction Open Drive -- one of the strongest trend day signals. Do not fade; trade with the direction.")
@OppositeBlock("VPOpenDriveShort")
@ForEngine("MT4,MT5,TS,MC,NT")
public class VPOpenDriveLong extends ConditionBlock {

    @Parameter
    public ChartData Chart;

    @Parameter(defaultValue = "Current", showIfDefault = false)
    @Editor(type = Editors.SelectionSymbols)
    public String Symbol;



    @Parameter(name = "Minimum Move", defaultValue = "10", minValue = 1, maxValue = 100, step = 1)
    @Help("Minimum cumulative upward move (in points) over DriveBars to confirm the drive")
    public int MinimumMove;

    @Parameter(defaultValue = "8", minValue = 0, maxValue = 23, step = 1)
    @Help("Session Open Hours")
    public int SessionStartHours;

    @Parameter(defaultValue = "30", minValue = 0, maxValue = 59, step = 1)
    @Help("Session Open Minutes")
    public int SessionStartMinutes;

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
    private SessionOHLCCalculator sessionCalculator = null;

    @Parameter(defaultValue = "1", minValue = 1, maxValue = 1)
    public int Shift;

    @Override
    protected void OnInit() throws BlockDefinitionException {
        sessionCalculator = new SessionOHLCCalculator(SessionOHLCCalculator.OPEN, SessionStartHours,
                SessionStartMinutes, SessionStartHours, SessionStartMinutes, Shift, Chart);
    }

    @Override
    public boolean OnBlockEvaluate() throws TradingException {
        double minMove = Strategy.convertPipsToRealPrice(Symbol, MinimumMove) / 10.0;

        // 3 consecutive bullish bars (close > open)
        if (Chart.Close(Shift) <= Chart.Open(Shift)) return false;
        if (Chart.Close(Shift + 1) <= Chart.Open(Shift + 1)) return false;
        if (Chart.Close(Shift + 2) <= Chart.Open(Shift + 2)) return false;

        // Cumulative move over the 3 bars must exceed MinimumMove
        return Chart.Close(Shift) - Chart.Open(Shift + 2) >= minMove;
    }

}
