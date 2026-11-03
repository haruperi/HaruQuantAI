package SQ.Blocks.Indicators.AnchoredVWAP;

import SQ.Internal.ConditionBlock;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.tradinglib.*;

@BuildingBlock(name="(AVWAP) Anchored VWAP is rising", display="AnchoredVWAP(@Chart@#SessionType#,#StdDevMult#)[#Shift#] is rising", returnType = ReturnTypes.Boolean)
@Help("Is triggered if Anchored VWAP is rising")
@ForEngine("MT4,MT5,TS,MC,NT")
@OppositeBlock("AnchoredVWAPFalling")
@ParameterSet(set="SessionType=1,StdDevMult=1.0")
@ParameterSet(set="SessionType=1,StdDevMult=2.0")
@ParameterSet(set="SessionType=2,StdDevMult=1.0")
@ParameterSet(set="SessionType=2,StdDevMult=2.0")
@ParameterSet(set="SessionType=3,StdDevMult=1.0")
@ParameterSet(set="SessionType=3,StdDevMult=2.0")
public class AnchoredVWAPRising extends ConditionBlock {
	
	@Parameter
	public ChartData Chart;
	
    @Parameter(defaultValue="1", name="SessionType")
    @Help("Anchor point for VWAP calculation")
    @Editor(type=Editors.Selection, values="Daily=1,Weekly=2,Monthly=3")
    public int SessionType;
    
    @Parameter(defaultValue="1.0", name="StdDevMult", minValue=0.5, maxValue=4.0, step=0.1)
    @Help("Standard deviation multiplier for bands")
    public double StdDevMult;

	@Parameter
	public int Shift;
	
	//------------------------------------------------------------------------
	//------------------------------------------------------------------------
	//------------------------------------------------------------------------
	
	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		AnchoredVWAP indicator = Strategy.Indicators.AnchoredVWAP(Chart, SessionType, StdDevMult);

		double curVal = indicator.VWAP.getRounded(Shift);
		double prevVal = indicator.VWAP.getRounded(Shift+1);
		
		return (curVal > prevVal);
	}

}