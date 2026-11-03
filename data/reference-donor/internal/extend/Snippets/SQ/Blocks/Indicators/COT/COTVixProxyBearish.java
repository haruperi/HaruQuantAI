/*
 * Copyright (c) 2026, StrategyQuant - All rights reserved.
 *
 * Code in this file was made in a good faith that it is correct and does what it should.
 * If you found a bug in this code OR you have an improvement suggestion OR you want to include
 * your own code snippet into our standard library please contact us at:
 * https://roadmap.strategyquant.com
 *
 * This code can be used only within StrategyQuant products.
 * Every owner of valid (free, trial or commercial) license of any StrategyQuant product
 * is allowed to freely use, copy, modify or make derivative work of this code without limitations,
 * to be used in all StrategyQuant products and share his/her modifications or derivative work
 * with the StrategyQuant community.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
 * PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES
 * OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 *
 */
package SQ.Blocks.Indicators.COT;

import SQ.Internal.ConditionBlock;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.BuildingBlock;
import com.strategyquant.tradinglib.OppositeBlock;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.ParameterSet;
import com.strategyquant.tradinglib.ReturnTypes;
import com.strategyquant.tradinglib.SortOrder;
import com.strategyquant.tradinglib.Help;
import com.strategyquant.tradinglib.ForEngine;

import com.strategyquant.tradinglib.data.CustomDataIndyMap;

/**
 * COT VIX Proxy Bearish — uses VIX COT to signal bearish conditions for equity indices.
 *
 * Logic: When VIX hedgers are at extreme LOW (smart money not hedging for vol)
 * AND VIX speculators are at extreme HIGH (crowd piling into vol bets), complacency → stocks FALL.
 */
@Help("VIX COT Proxy Bearish — uses VIX futures COT instead of direct index COT for equity index trading. " +
	"BEARISH signal: VIX hedgers at extreme LOW (smart money complacent, not hedging) " +
	"AND VIX speculators at extreme HIGH (crowd positioned for vol = complacent about stocks). " +
	"Markets: Best for ES, NQ, YM, RTY. Uses VX (VIX futures) COT data. " +
	"Remember: VIX is inverse to stocks — low VIX hedger CPI = BEARISH for equities. " +
	"Pavel's research: direct stock index COT is less reliable; VIX COT may be more predictive. — COT data provided by SpreadCharts.com")
@BuildingBlock(name="COT VIX Proxy Bearish", display="COTVixBear(#CotSymbol#, hedg<#HedgerThreshold#, spec>#SpecThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(111)
@OppositeBlock(value="COTVixProxyBullish")
@ParameterSet(set="CotSymbol=VX,Period=52w")
@ParameterSet(set="CotSymbol=VX,Period=156w")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTVixProxyBearish extends ConditionBlock {

	@Parameter(defaultValue="VX", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.20", minValue=0.00, maxValue=0.50, step=0.05, name="VIX Hedger Low Threshold")
	public double HedgerThreshold;

	@Parameter(defaultValue="0.80", minValue=0.50, maxValue=1.00, step=0.05, name="VIX Speculator High Threshold")
	public double SpecThreshold;

	@Parameter(defaultValue="156w", name="Period (52w or 156w)")
	public String Period;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg, mapSpec;
	private boolean dataReady = false;

	//------------------------------------------------------------------------

	@Override
	protected void OnInit() {
		try {
			// VX (VIX futures) by default, the CotSymbol parameter can point to another volatility contract
			if(CotSymbol == null || CotSymbol.trim().isEmpty()) {
				// the Builder leaves the free-text symbol empty, VX is the default and the exports need it in the XML
				CotSymbol = "VX";
				COTCompositeScore.persistEmptyCotSymbolToXml(Strategy, getClass().getSimpleName(), "VX");
			}
			String vixSymbol = CotSymbol.trim();
			String name = COTCompositeScore.findCotIndicatorName(vixSymbol, Period.toUpperCase());

			if(name != null) {
				mapHedg = COTCompositeScore.loadMap(name, 0);
				mapSpec = COTCompositeScore.loadMap(name, 2);
			}

			dataReady = (mapHedg != null && mapSpec != null);

			if(!dataReady) {
				Log.error("COTVixProxyBearish: VIX COT data not found for period {}. Make sure VX COT data is loaded.", Period);
			}
		} catch(Exception e) {
			Log.error("COTVixProxyBearish OnInit error", e);
		}
	}

	//------------------------------------------------------------------------

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		if(!dataReady) return false;

		long barTime = Strategy.MarketData.Chart(0).Time(Shift);

		double hedg = mapHedg.getTime(barTime);
		double spec = mapSpec.getTime(barTime);

		// VIX hedgers low + VIX specs high → expect vol to rise → stocks bearish
		return (hedg < HedgerThreshold && spec > SpecThreshold);
	}
}
