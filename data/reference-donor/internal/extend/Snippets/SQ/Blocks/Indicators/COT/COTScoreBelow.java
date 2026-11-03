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
 * COT Score Below condition block (Strategy 5 - regime filter).
 *
 * Returns true when the COT Composite Score is below a threshold,
 * indicating a bearish positioning regime.
 *
 * Typical usage: allow short trades when COTScore < -0.60
 */
@Help("COT Composite Score Below threshold (Bearish regime). Score < threshold indicates institutional bearish positioning. Use as a regime filter to allow short trades. (Strategy 5 mirror) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="COT Score Below", display="COTScore(#CotSymbol#) < #Level#", returnType = ReturnTypes.Boolean)
@SortOrder(201)
@OppositeBlock(value="COTScoreAbove")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTScoreBelow extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="-0.60", minValue=-0.95, maxValue=-0.10, step=0.05, name="Score Threshold")
	public double Level;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg52, mapHedg156, mapSpec52, mapSpec156;
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
		
					String name52  = COTCompositeScore.findCotIndicatorName(CotSymbol, "52W");
					String name156 = COTCompositeScore.findCotIndicatorName(CotSymbol, "156W");
		
					if(name52 != null) {
						mapHedg52 = COTCompositeScore.loadMap(name52, 0);
						mapSpec52 = COTCompositeScore.loadMap(name52, 2);
					}
		
					if(name156 != null) {
						mapHedg156 = COTCompositeScore.loadMap(name156, 0);
						mapSpec156 = COTCompositeScore.loadMap(name156, 2);
					}
		
					dataReady = (mapHedg52 != null && mapHedg156 != null && mapSpec52 != null && mapSpec156 != null);
				} catch(Exception e) {
					Log.error("COTScoreBelow OnInit error", e);
				}
	}

	//------------------------------------------------------------------------

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime = Strategy.MarketData.Chart(0).Time(Shift);

		double hedg52  = mapHedg52.getTime(barTime);
		double hedg156 = mapHedg156.getTime(barTime);
		double spec52  = mapSpec52.getTime(barTime);
		double spec156 = mapSpec156.getTime(barTime);

		double score = ((hedg52 + hedg156) / 2.0) - ((spec52 + spec156) / 2.0);

		return (score < Level);
	}
}
