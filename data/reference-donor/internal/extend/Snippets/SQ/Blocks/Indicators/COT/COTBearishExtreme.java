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
 * COT Bearish Extreme condition block (Strategy 1 mirror).
 *
 * Returns true when hedgers are at an extreme low AND speculators at an extreme high,
 * indicating a bearish COT regime.
 *
 * Conditions:
 *   cpihedg_52w  < HedgerThreshold  (default 0.10)
 *   cpispec_52w  > SpecThreshold   (default 0.90)
 *   cpihedg_156w < Hedger156Threshold  (default 0.25)
 *   cpispec_156w > Spec156Threshold   (default 0.75)
 */
@Help("Hedger vs Speculator Extreme Reversal (Bearish). Hedgers at extreme low CPI AND speculators at extreme high CPI on the 52-week window. Mirror of Strategy 1. This rare divergence historically precedes major bearish reversals. (Strategy 2) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="COT Bearish Extreme", display="COTBearish(#CotSymbol#, hedg<#HedgerThreshold#, spec>#SpecThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(101)
@OppositeBlock(value="COTBullishExtreme")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTBearishExtreme extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.10", minValue=0.00, maxValue=0.50, step=0.05, name="Hedger Low Threshold (52w)")
	public double HedgerThreshold;

	@Parameter(defaultValue="0.90", minValue=0.50, maxValue=1.00, step=0.05, name="Speculator High Threshold (52w)")
	public double SpecThreshold;

	@Parameter(defaultValue="0.25", minValue=0.00, maxValue=0.60, step=0.05, name="Hedger Low Threshold (156w)")
	public double Hedger156Threshold;

	@Parameter(defaultValue="0.75", minValue=0.40, maxValue=1.00, step=0.05, name="Speculator High Threshold (156w)")
	public double Spec156Threshold;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg52, mapSpec52, mapHedg156, mapSpec156;
	private boolean dataReady = false;
	private boolean has156w = false;

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
						has156w = (mapHedg156 != null && mapSpec156 != null);
					}
		
					dataReady = (mapHedg52 != null && mapSpec52 != null);
				} catch(Exception e) {
					Log.error("COTBearishExtreme OnInit error", e);
				}
	}

	//------------------------------------------------------------------------

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime = Strategy.MarketData.Chart(0).Time(Shift);

		double hedg52 = mapHedg52.getTime(barTime);
		double spec52 = mapSpec52.getTime(barTime);

		// Primary 52w conditions (bearish mirror)
		if(hedg52 >= HedgerThreshold || spec52 <= SpecThreshold) {
			return false;
		}

		// Optional 156w structural confirmation
		if(has156w) {
			double hedg156 = mapHedg156.getTime(barTime);
			double spec156 = mapSpec156.getTime(barTime);

			if(hedg156 >= Hedger156Threshold || spec156 <= Spec156Threshold) {
				return false;
			}
		}

		return true;
	}
}
