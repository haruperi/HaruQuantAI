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
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.ParameterSet;
import com.strategyquant.tradinglib.ReturnTypes;
import com.strategyquant.tradinglib.SortOrder;
import com.strategyquant.tradinglib.Help;
import com.strategyquant.tradinglib.ForEngine;

import com.strategyquant.tradinglib.data.CustomDataIndyMap;

/**
 * COT Extreme Persistence (Strategies 7 + 23).
 *
 * Checks whether a COT extreme has been maintained for at least N consecutive weeks.
 * Direction=1: bullish extreme persistence (H52 > ExtremeThreshold for N weeks)
 * Direction=-1: bearish extreme persistence (S52 > ExtremeThreshold for N weeks)
 *
 * A persistent extreme may confirm strong structural pressure.
 * An extreme lasting one week is different from one lasting six weeks.
 *
 * Can be used two ways:
 *   - Young extremes (MinWeeks=1-2): fresh signal, act quickly
 *   - Mature extremes (MinWeeks=4-6): strong structural pressure, higher conviction
 *
 * Sources: Briese COT Index [R2].
 */
@Help("Extreme Persistence. Checks if an extreme has persisted for N consecutive weeks. Direction=1: bullish H52 persistence. Direction=-1: bearish S52 persistence. Young vs mature extremes give different signals. (Strategy 7+23) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT12) Extreme Persistence", display="COTPersist(#CotSymbol#, dir=#Direction#, weeks>=#MinWeeks#)", returnType = ReturnTypes.Boolean)
@SortOrder(1200)
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTExtremePersistence extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="1", minValue=-1, maxValue=1, step=2, name="Direction (1=bullish H52, -1=bearish S52)")
	public int Direction;

	@Parameter(defaultValue="0.90", minValue=0.80, maxValue=0.99, step=0.05, name="Extreme Threshold")
	public double ExtremeThreshold;

	@Parameter(defaultValue="3", minValue=1, maxValue=12, step=1, name="Min Consecutive Weeks")
	public int MinWeeks;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg52, mapSpec52;
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
						mapSpec52 = COTCompositeScore.loadMap(name52, 2);
					}
					dataReady = (mapHedg52 != null && mapSpec52 != null);
				} catch(Exception e) {
					Log.error("COTExtremePersistence OnInit error", e);
				}
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		CustomDataIndyMap map = (Direction > 0) ? mapHedg52 : mapSpec52;

		// Count consecutive weeks at extreme
		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		long WEEK_MS = 7L * 24 * 3600 * 1000;
		for(int i = 0; i < MinWeeks; i++) {
			long t = barTime - i * WEEK_MS;
			double val = map.getTime(t);

			if(Direction > 0) {
				// Bullish: hedger must be above extreme
				if(val < ExtremeThreshold) return false;
			} else {
				// Bearish: speculator must be above extreme (crowded long)
				if(val < ExtremeThreshold) return false;
			}
		}

		return true; // All MinWeeks consecutive weeks were at extreme
	}
}
