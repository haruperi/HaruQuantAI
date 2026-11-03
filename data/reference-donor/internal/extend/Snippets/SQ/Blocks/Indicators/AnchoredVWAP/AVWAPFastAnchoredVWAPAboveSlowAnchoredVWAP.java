package SQ.Blocks.Indicators.AnchoredVWAP;

import SQ.Internal.ConditionBlock;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.tradinglib.*;

@BuildingBlock(name="(AVWAP) Faster Anchored VWAP is above Slower Anchored VWAP", display="Faster AnchoredVWAP(@Chart@#FastSessionType#,#FastStdDevMult#)[#Shift#] is above Slower AnchoredVWAP(@Chart@#SlowSessionType#,#SlowStdDevMult#)[#Shift#]", returnType = ReturnTypes.Boolean)
@Help("Is triggered if Faster Anchored VWAP is above Slower Anchored VWAP")
@ForEngine("MT4,MT5,TS,MC,NT")
@OppositeBlock("AVWAPFastAnchoredVWAPBelowSlowAnchoredVWAP")
@ParameterSet(set="FastSessionType=1,FastStdDevMult=1.0,SlowSessionType=2,SlowStdDevMult=1.0")
@ParameterSet(set="FastSessionType=1,FastStdDevMult=1.0,SlowSessionType=3,SlowStdDevMult=1.0")
@ParameterSet(set="FastSessionType=1,FastStdDevMult=2.0,SlowSessionType=2,SlowStdDevMult=2.0")
@ParameterSet(set="FastSessionType=2,FastStdDevMult=1.0,SlowSessionType=3,SlowStdDevMult=1.0")
@MT5ExtendedTemplate
public class AVWAPFastAnchoredVWAPAboveSlowAnchoredVWAP extends ConditionBlock {
	
	@Parameter
	public ChartData Chart;
	
    @Parameter(defaultValue="1", name="FastSessionType")
    @Help("Anchor point for fast VWAP calculation")
    @Editor(type=Editors.Selection, values="Daily=1,Weekly=2,Monthly=3")
    public int FastSessionType;
    
    @Parameter(defaultValue="1.0", name="FastStdDevMult", minValue=0.5, maxValue=4.0, step=0.1)
    @Help("Standard deviation multiplier for fast VWAP bands")
    public double FastStdDevMult;
    
    @Parameter(defaultValue="2", name="SlowSessionType")
    @Help("Anchor point for slow VWAP calculation")
    @Editor(type=Editors.Selection, values="Daily=1,Weekly=2,Monthly=3")
    public int SlowSessionType;
    
    @Parameter(defaultValue="1.0", name="SlowStdDevMult", minValue=0.5, maxValue=4.0, step=0.1)
    @Help("Standard deviation multiplier for slow VWAP bands")
    public double SlowStdDevMult;
	

	@Parameter
	public int Shift;
	
	//------------------------------------------------------------------------
	//------------------------------------------------------------------------
	//------------------------------------------------------------------------
	
	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		AnchoredVWAP fastIndicator = Strategy.Indicators.AnchoredVWAP(Chart, FastSessionType, FastStdDevMult);
		AnchoredVWAP slowIndicator = Strategy.Indicators.AnchoredVWAP(Chart, SlowSessionType, SlowStdDevMult);

		double fastVal = fastIndicator.VWAP.getRounded(Shift);
		double slowVal = slowIndicator.VWAP.getRounded(Shift);
		
		return (fastVal > slowVal);
	}

}