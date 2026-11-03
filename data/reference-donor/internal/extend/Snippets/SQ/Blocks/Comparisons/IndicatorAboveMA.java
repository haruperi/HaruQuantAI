// IndicatorAboveMA implementation
package SQ.Blocks.Comparisons;

import com.strategyquant.lib.*;
import com.strategyquant.datalib.*;
import com.strategyquant.tradinglib.*;

// Only the engines that have a template for this block - an engine offered it without one
// degrades the export silently.
@ForEngine("MT4,MT5,TS,MC,NT")
@BuildingBlock(name="(I > MA) Indicator Above MA", display="#Indicator# is above its #MAType# MA(#Period#)", returnType = ReturnTypes.Boolean)
@OppositeBlock("IndicatorBelowMA")
public class IndicatorAboveMA extends IndicatorMAComparisonBlockAbstract {
    
    @Override
    public boolean OnEvaluateComparison() throws TradingException {
        double indicatorValue = SQUtils.round(Indicator.evaluateBlock(Shift), 6);
        double maValue = calculateMA(Period, MAType, Shift);
        return indicatorValue > maValue;
    }
}