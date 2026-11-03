package SQ.Formulas.RangeLevel;

import SQ.Internal.FormulaBlock;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.tradinglib.*;

@Formula(order=200, name="Fixed value (in pips)", formula="RangeLevel")
public class FixedValue extends FormulaBlock {

	@Parameter(defaultValue="50", minValue=1, builderMinValue=5, builderMaxValue=500, maxValue=9999999, step=1, postfix="pips")
	@SLPTValue(SLPTValues.ValueInPips)
	public double Value;
	
	//------------------------------------------------------------------------
	//------------------------------------------------------------------------
	//------------------------------------------------------------------------
	
	public double evaluateFormula(StrategyBase strategy, String symbol, double price, int direction) throws TradingException {		
		double valueInRealPrice = strategy.convertPipsToRealPrice(symbol, Value);

		// Anchored on the price the strategy decides on (StrategyBase.decisionBid / decisionAsk).
		if(direction == Directions.Long) {
			// long order
			return (strategy.decisionBid(symbol, 0) - valueInRealPrice);

		} else {
			// short order
			return (strategy.decisionAsk(symbol, 0) + valueInRealPrice);
		}
	}
}
