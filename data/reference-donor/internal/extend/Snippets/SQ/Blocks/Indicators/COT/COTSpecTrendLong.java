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
 * COT Speculator Trend Following — Long (Strategy 4 + 12).
 *
 * Instead of fading speculators, this strategy follows them when they are in
 * a moderate trend zone — not yet extreme, but clearly committed directionally.
 *
 * Long conditions:
 *   S52 > SpecMin (default 0.60) — speculators clearly long
 *   S52 < SpecMax (default 0.90) — but NOT at extreme crowded levels
 *   S156 > Spec156Threshold (default 0.55) — structural confirmation
 *   S52 > S52[Lookback] — positioning still improving (rising)
 *
 * The non-extreme zone is key: this tests the hypothesis that moderate
 * speculative conviction is often RIGHT, unlike extreme crowding which
 * often precedes reversals.
 *
 * Sources: Wang 2001 [R6], Wang 2004 [R7], Sanders et al. 2004 [R8], Moskowitz et al. 2012 [R11].
 */
@Help("Speculator Trend Following (Long). Follows moderate speculator conviction (not yet extreme). S52 in [SpecMin,SpecMax] band, S156 > structural minimum, S52 rising. (Strategy 4+12) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT08) Spec Trend Long", display="COTSpecTrendL(#CotSymbol#, s52>#SpecMin#<#SpecMax#)", returnType = ReturnTypes.Boolean)
@SortOrder(800)
@OppositeBlock(value="COTSpecTrendShort")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTSpecTrendLong extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.60", minValue=0.40, maxValue=0.80, step=0.05, name="Spec Min (52w)")
	public double SpecMin;

	@Parameter(defaultValue="0.90", minValue=0.80, maxValue=0.99, step=0.05, name="Spec Max (52w)")
	public double SpecMax;

	@Parameter(defaultValue="0.55", minValue=0.40, maxValue=0.80, step=0.05, name="Spec Min (156w)")
	public double Spec156Threshold;

	@Parameter(defaultValue="4", minValue=1, maxValue=12, step=1, name="Lookback Weeks")
	public int Lookback;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapSpec52, mapSpec156;
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
		
					String name52  = COTCompositeScore.findCotIndicatorName(CotSymbol, "52W");
					String name156 = COTCompositeScore.findCotIndicatorName(CotSymbol, "156W");
		
					if(name52 != null) {
						mapSpec52 = COTCompositeScore.loadMap(name52, 2);
					}
					if(name156 != null) {
						mapSpec156 = COTCompositeScore.loadMap(name156, 2);
					}
		
					dataReady = (mapSpec52 != null && mapSpec156 != null);
				} catch(Exception e) {
					Log.error("COTSpecTrendLong OnInit error", e);
				}
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime     = Strategy.MarketData.Chart(0).Time(Shift);
		long prevBarTime = Strategy.MarketData.Chart(0).Time(Shift + Lookback);

		double spec52Now  = mapSpec52.getTime(barTime);
		double spec52Prev = mapSpec52.getTime(prevBarTime);
		double spec156Now = mapSpec156.getTime(barTime);

		// Spec in moderate trend zone, rising, with structural confirmation
		return (spec52Now > SpecMin && spec52Now < SpecMax && spec156Now > Spec156Threshold && spec52Now > spec52Prev);
	}
}
