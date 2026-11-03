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
 * COT 52w vs 156w Positioning Shift — Bearish (Strategy 3 mirror).
 *
 * Detects when recent (52w) positioning diverges bearishly from structural (156w) positioning.
 * HedgerShift = H52 - H156 < -ShiftThreshold  (hedgers recently LESS bullish)
 * SpecShift   = S52 - S156 > ShiftThreshold    (speculators recently MORE bullish)
 *
 * Sources: Briese COT Index [R2], Movement Index [R3].
 */
@Help("52w vs 156w Positioning Shift (Bearish). Hedgers recently LESS bullish, speculators recently MORE bullish than structural baseline. (Strategy 3 mirror) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT07) 52v156 Shift Bearish", display="COT52v156Bear(#CotSymbol#, shift>#ShiftThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(700)
@OppositeBlock(value="COT52vs156ShiftBullish")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COT52vs156ShiftBearish extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.15", minValue=0.05, maxValue=0.50, step=0.05, name="Shift Threshold")
	public double ShiftThreshold;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg52, mapSpec52, mapHedg156, mapSpec156;
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
						mapHedg52 = COTCompositeScore.loadMap(name52, 0);
						mapSpec52 = COTCompositeScore.loadMap(name52, 2);
					}
		
					if(name156 != null) {
						mapHedg156 = COTCompositeScore.loadMap(name156, 0);
						mapSpec156 = COTCompositeScore.loadMap(name156, 2);
					}
		
					dataReady = (mapHedg52 != null && mapSpec52 != null && mapHedg156 != null && mapSpec156 != null);
				} catch(Exception e) {
					Log.error("COT52vs156ShiftBearish OnInit error", e);
				}
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime = Strategy.MarketData.Chart(0).Time(Shift);

		double hedg52  = mapHedg52.getTime(barTime);
		double spec52  = mapSpec52.getTime(barTime);
		double hedg156 = mapHedg156.getTime(barTime);
		double spec156 = mapSpec156.getTime(barTime);

		double hedgerShift = hedg52 - hedg156;
		double specShift   = spec52 - spec156;

		// Bearish: hedgers recently LESS bullish, speculators recently MORE bullish
		return (hedgerShift < -ShiftThreshold && specShift > ShiftThreshold);
	}
}
