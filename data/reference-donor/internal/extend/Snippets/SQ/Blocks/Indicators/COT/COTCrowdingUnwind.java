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
 * COT Crowding Unwind condition block (Strategy 2).
 *
 * Detects when speculator positioning WAS at an extreme and is now beginning to unwind.
 *
 * Bearish unwind (after long crowding):
 *   cpispec_52w was > SpecExtreme recently
 *   cpispec_52w is now falling (current < previous)
 *
 * Bullish unwind (after short crowding):
 *   cpispec_52w was < (1 - SpecExtreme) recently
 *   cpispec_52w is now rising (current > previous)
 *
 * The Direction parameter controls which side: 1 = bearish unwind (short after long crowd),
 * -1 = bullish unwind (long after short crowd).
 */
@Help("Crowding Unwind. Detects when a crowded positioning extreme is unwinding. The previously crowded group has moved past its normalize threshold and is still moving away from the extreme. (Strategy 8) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="COT Crowding Unwind", display="COTUnwind(#CotSymbol#, dir=#Direction#, ext=#SpecExtreme#)", returnType = ReturnTypes.Boolean)
@SortOrder(300)
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTCrowdingUnwind extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="1", minValue=-1, maxValue=1, step=2, name="Direction (1=bear unwind, -1=bull unwind)")
	public int Direction;

	@Parameter(defaultValue="0.90", minValue=0.70, maxValue=0.99, step=0.05, name="Speculator Extreme Threshold")
	public double SpecExtreme;

	@Parameter(defaultValue="0.25", minValue=0.05, maxValue=0.50, step=0.05, name="Hedger Opposing Threshold")
	public double HedgerOpposing;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapSpec52, mapHedg52;
	private boolean dataReady = false;

	//------------------------------------------------------------------------

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
						mapSpec52 = COTCompositeScore.loadMap(name52, 2); // cpispec
						mapHedg52 = COTCompositeScore.loadMap(name52, 0); // cpihedg
					}
		
					dataReady = (mapSpec52 != null && mapHedg52 != null);
				} catch(Exception e) {
					Log.error("COTCrowdingUnwind OnInit error", e);
				}
	}

	//------------------------------------------------------------------------

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		// We need current and previous week bar times
		// Since COT is weekly, we look 1 shift back for "previous"
		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		long prevBarTime = barTime - 7L * 24 * 3600 * 1000;

		double specNow  = mapSpec52.getTime(barTime);
		double specPrev = mapSpec52.getTime(prevBarTime);
		double hedgNow  = mapHedg52.getTime(barTime);

		if(Direction > 0) {
			// Bearish unwind: speculators WERE crowded long, now falling
			// specPrev was at extreme, now spec is falling, hedgers are opposing
			return (specPrev > SpecExtreme && specNow < specPrev && hedgNow < HedgerOpposing);
		} else {
			// Bullish unwind: speculators WERE crowded short, now rising
			double shortExtreme = 1.0 - SpecExtreme;
			double hedgerHigh = 1.0 - HedgerOpposing;
			return (specPrev < shortExtreme && specNow > specPrev && hedgNow > hedgerHigh);
		}
	}
}
