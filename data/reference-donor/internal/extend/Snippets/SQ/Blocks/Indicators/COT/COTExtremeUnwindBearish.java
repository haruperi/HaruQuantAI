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
 * COT Extreme Unwind — Bearish (Strategy 8 mirror).
 *
 * Detects when a bullish COT extreme has occurred and hedger positioning
 * is now normalizing. Hedgers WERE extremely bullish, now retreating.
 *
 * Conditions:
 *   Highest(H52, LookbackWeeks) > CrowdedThreshold — hedgers WERE extremely bullish
 *   H52 < NormalizeThreshold — hedgers have retreated past normalize level
 *   H52 < H52[1] — still falling
 *
 * Sources: Briese COT Index [R2], Movement Index [R3], Wang 2001 [R6].
 */
@Help("Extreme Unwind (Bearish). Hedger was extremely bullish, now retreating past normalize level. (Strategy 8 mirror) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT14) Extreme Unwind Bearish", display="COTUnwindBear(#CotSymbol#, crowd>#CrowdedThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(1400)
@OppositeBlock(value="COTExtremeUnwindBullish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTExtremeUnwindBearish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.95", minValue=0.85, maxValue=0.99, step=0.05, name="Hedger Crowded Threshold")
	public double CrowdedThreshold;

	@Parameter(defaultValue="0.80", minValue=0.50, maxValue=0.92, step=0.05, name="Normalize Threshold")
	public double NormalizeThreshold;

	@Parameter(defaultValue="6", minValue=2, maxValue=12, step=1, name="Lookback Weeks")
	public int LookbackWeeks;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg52;
	private boolean dataReady = false;

	@Override
	protected void OnInit() {
		// No-op: Strategy not yet available during initialize()
	}

	//------------------------------------------------------------------------

	private boolean initialized = false;

	private void lazyInit() {
		if(initialized) return;
		initialized = true;

		if(Strategy == null) return;

		CotSymbol = COTCompositeScore.resolveBlockSymbol(Strategy, CotSymbol);

		try {
		
					String name52 = COTCompositeScore.findCotIndicatorName(CotSymbol, "52W");
					if(name52 != null) {
						mapHedg52 = COTCompositeScore.loadMap(name52, 0);
					}
					dataReady = (mapHedg52 != null);
				} catch(Exception e) {
					Log.error("COTExtremeUnwindBearish OnInit error", e);
				}
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime     = Strategy.MarketData.Chart(0).Time(Shift);
		long WEEK_MS     = 7L * 24 * 3600 * 1000;
		long prevBarTime = barTime - WEEK_MS;

		double hedg52Now  = mapHedg52.getTime(barTime);
		double hedg52Prev = mapHedg52.getTime(prevBarTime);

		// Must be below normalize threshold AND still falling
		if(hedg52Now >= NormalizeThreshold || hedg52Now >= hedg52Prev) return false;

		// Check if hedger was extremely bullish in the lookback window
		for(int i = 1; i <= LookbackWeeks; i++) {
			long pastTime = barTime - i * WEEK_MS;
			double pastVal = mapHedg52.getTime(pastTime);
			if(pastVal > CrowdedThreshold) {
				return true;
			}
		}

		return false;
	}
}
