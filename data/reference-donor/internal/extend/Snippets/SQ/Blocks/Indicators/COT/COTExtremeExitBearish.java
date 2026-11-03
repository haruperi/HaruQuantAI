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
 * COT Extreme Exit — Bearish (Strategies 6 + 24 mirror).
 *
 * Trades the transition OUT of a bearish COT extreme.
 * Speculator was at extreme high (crowded long), now leaving.
 *
 * Conditions:
 *   Highest(S52, LookbackWeeks) > ExtremeThreshold — spec WAS crowded long
 *   S52 < ExitThreshold — spec now leaving the extreme
 *
 * Sources: Briese COT Index [R2], Movement Index [R3].
 */
@Help("Extreme Exit (Bearish). Speculator was crowded long, now normalizing below exit threshold. (Strategy 6+24 mirror) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT11) Extreme Exit Bearish", display="COTExitBear(#CotSymbol#, ext>#ExtremeThreshold#, exit<#ExitThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(1100)
@OppositeBlock(value="COTExtremeExitBullish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTExtremeExitBearish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.95", minValue=0.85, maxValue=0.99, step=0.05, name="Spec Extreme Threshold (S52)")
	public double ExtremeThreshold;

	@Parameter(defaultValue="0.85", minValue=0.60, maxValue=0.92, step=0.05, name="Spec Exit Threshold (S52)")
	public double ExitThreshold;

	@Parameter(defaultValue="6", minValue=2, maxValue=12, step=1, name="Lookback Weeks")
	public int LookbackWeeks;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapSpec52;
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
						mapSpec52 = COTCompositeScore.loadMap(name52, 2);
					}
					dataReady = (mapSpec52 != null);
				} catch(Exception e) {
					Log.error("COTExtremeExitBearish OnInit error", e);
				}
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		double spec52Now = mapSpec52.getTime(barTime);

		// Current spec must be below exit threshold (leaving the crowded-long extreme)
		if(spec52Now >= ExitThreshold) return false;

		// Check if spec extreme occurred in the lookback window
		long WEEK_MS = 7L * 24 * 3600 * 1000;
		for(int i = 1; i <= LookbackWeeks; i++) {
			long pastTime = barTime - i * WEEK_MS;
			double pastVal = mapSpec52.getTime(pastTime);
			if(pastVal > ExtremeThreshold) {
				return true; // Spec was crowded long, now leaving
			}
		}

		return false;
	}
}
