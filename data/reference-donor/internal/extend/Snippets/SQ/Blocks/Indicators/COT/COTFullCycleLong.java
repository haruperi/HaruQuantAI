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
import com.strategyquant.tradinglib.*;

import com.strategyquant.tradinglib.data.CustomDataIndyMap;

/**
 * COT Full-Cycle Long Entry (Strategy 39).
 *
 * Cycle strategy: enter long when hedger CPI crosses an entry threshold upward.
 *   COT[t-1] < EntryLevel AND COT[t] >= EntryLevel -> BUY
 *
 * Typical entry thresholds: 0.10, 0.20, 0.30
 * Then hold for weeks/months until exit threshold reached.
 *
 * Intended as one component within a multi-factor system, not as a standalone edge.
 */
@Help("COT Full-Cycle Long Entry (Strategy 39). Enter long when hedger CPI crosses the EntryLevel upward: " +
	"previous bar COT < EntryLevel AND current bar COT >= EntryLevel. " +
	"Designed for position trading: hold for weeks/months until exit level reached. " +
	"Recommended entry thresholds to test: 0.10, 0.20, 0.30. " +
	"Pair with COTFullCycleExitLong for the complete cycle strategy. — COT data provided by SpreadCharts.com")
@BuildingBlock(name="COT Full-Cycle Long Entry", display="COTCycleLong(#CotSymbol#, entry=#EntryLevel#)", returnType = ReturnTypes.Boolean)
@SortOrder(120)
@OppositeBlock(value="COTFullCycleShort")
@ParameterSet(set="CotSymbol=AUTO,Period=52w")
@ParameterSet(set="CotSymbol=AUTO,Period=156w")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTFullCycleLong extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.20", minValue=0.05, maxValue=0.50, step=0.05, name="Entry Level (COT crosses up)")
	public double EntryLevel;

	@Parameter(defaultValue="156w", name="Period (52w or 156w)")
	public String Period;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg;
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
		
					String name = COTCompositeScore.findCotIndicatorName(CotSymbol, Period.toUpperCase());
					if(name != null) {
						mapHedg = COTCompositeScore.loadMap(name, 0);  // cpihedg
					}
		
					dataReady = (mapHedg != null);
				} catch(Exception e) {
					Log.error("COTFullCycleLong OnInit error", e);
				}
	}

	//------------------------------------------------------------------------

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime = Strategy.MarketData.Chart(0).Time(Shift);
		long prevBarTime = Strategy.MarketData.Chart(0).Time(Shift + 1);

		double cotNow  = mapHedg.getTime(barTime);
		double cotPrev = mapHedg.getTime(prevBarTime);

		// Crossover: previous below entry, current at or above entry
		return (cotPrev < EntryLevel && cotNow >= EntryLevel);
	}
}
