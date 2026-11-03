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

import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.BuildingBlock;
import com.strategyquant.tradinglib.Colors;
import com.strategyquant.tradinglib.Indicator;
import com.strategyquant.tradinglib.Output;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.ParameterSet;
import com.strategyquant.tradinglib.ReturnTypes;
import com.strategyquant.tradinglib.Help;
import com.strategyquant.tradinglib.ForEngine;

import SQ.Internal.IndicatorBlock;

import com.strategyquant.tradinglib.data.CustomDataIndyMap;

/**
 * COT Hedger-Speculator Spread indicator block.
 *
 * Returns the difference: Hedger_CPI - Speculator_CPI for the selected window.
 * Positive = hedgers more bullish than speculators (contrarian bullish).
 * Negative = speculators more bullish than hedgers (contrarian bearish).
 *
 * Range: -1 to +1.
 */
@Help("COT Hedger-Speculator Spread. The difference between Hedger CPI and Speculator CPI for a single lookback window. " +
	"Range: -1 to +1. " +
	"Value > 0 (positive): Hedgers more bullish than speculators — institutional BULLISH divergence — favor LONG trades. " +
	"Value = 0: Hedgers and speculators equally positioned — neutral. " +
	"Value < 0 (negative): Speculators more bullish than hedgers — speculative excess — favor SHORT trades. " +
	"Large positive values (above +0.4) indicate strong smart-money bullishness vs dumb-money bearishness. " +
	"Large negative values (below -0.4) indicate speculative euphoria that often precedes reversals. " +
	"This is the most direct measure of the institutional vs speculative positioning gap. — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT) Hedger-Spec Spread", display="COT_Spread(#CotSymbol#,#Period#)[#Shift#]", returnType = ReturnTypes.Number)
@Indicator(oscillator=true, middleValue=0, min=-1, max=1, step=0.01)
@ParameterSet(set="CotSymbol=AUTO,Period=52w")
@ParameterSet(set="CotSymbol=AUTO,Period=156w")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTHedgerSpecSpread extends IndicatorBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="156w", name="Period (52w or 156w)")
	public String Period;

	@Output(name = "HedgSpecSpread", color = Colors.DeepSkyBlue)
	public com.strategyquant.datalib.DataSeries Value;

	private CustomDataIndyMap mapHedg;
	private CustomDataIndyMap mapSpec;
	private boolean dataReady = false;

	//------------------------------------------------------------------------

	@Override
	protected void OnInit() throws TradingException {
		// No-op: Strategy not yet available during initialize()
	}

	@Override
	protected void OnBarUpdate() throws TradingException {
		// Not used - OnBlockEvaluate is overridden
	}

	//------------------------------------------------------------------------

	private boolean initialized = false;

	private void lazyInit() {
		if(initialized) return;
		initialized = true;

		if(Strategy == null) return;

		CotSymbol = COTCompositeScore.resolveBlockSymbol(Strategy, CotSymbol);

		
				String name = COTCompositeScore.findCotIndicatorName(CotSymbol, Period.toUpperCase());
				if(name != null) {
					mapHedg = COTCompositeScore.loadMap(name, 0);  // cpihedg = 0
					mapSpec = COTCompositeScore.loadMap(name, 2);  // cpispec = 2
				}
				dataReady = (mapHedg != null && mapSpec != null);
		
				if(!dataReady) {
					Log.warn("COTHedgerSpecSpread: Could not load data for {} {}", CotSymbol, Period);
				}
	}

	//------------------------------------------------------------------------

	@Override
	public double OnBlockEvaluate(int relativeShift) throws TradingException {
		lazyInit();

		if(!dataReady || Strategy == null) {
			return 0;
		}

		long barTime = Strategy.MarketData.Chart(0).Time(relativeShift + Shift);
		double hedg = mapHedg.getTime(barTime);
		double spec = mapSpec.getTime(barTime);
		return hedg - spec;
	}
}
