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
 * COT Speculator CPI (cpispec) indicator block.
 *
 * Returns the normalized large-speculator positioning index (0.0 to 1.0).
 * 0.0 = at the most net-short of the lookback range,
 * 1.0 = at the most net-long of the lookback range.
 */
@Help("COT Speculator CPI (Commitment Percentile Index). Measures where large speculator net positioning ranks within its historical range over the selected lookback window (52w or 156w). " +
	"Range: 0 to 1. " +
	"Value = 0: Speculators at their MOST NET-SHORT — crowd is maximally bearish — contrarian BULLISH signal. " +
	"Value = 0.5: Speculators at the median — neutral. " +
	"Value = 1: Speculators at their MOST NET-LONG — crowd is maximally bullish — contrarian BEARISH signal. " +
	"Speculators (managed money, hedge funds) are trend-followers and often considered DUMB MONEY at extremes. " +
	"When speculators are at one extreme while hedgers are at the opposite extreme, it creates the strongest contrarian signals. — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT) Speculator CPI", display="COT_Spec(#CotSymbol#,#Period#)[#Shift#]", returnType = ReturnTypes.Number)
@Indicator(oscillator=true, middleValue=0.5, min=0, max=1, step=0.01)
@ParameterSet(set="CotSymbol=AUTO,Period=52w")
@ParameterSet(set="CotSymbol=AUTO,Period=156w")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTCpispec extends IndicatorBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="156w", name="Period (52w or 156w)")
	public String Period;

	@Output(name = "cpispec", color = Colors.Green)
	public com.strategyquant.datalib.DataSeries Value;

	private CustomDataIndyMap map;
	private boolean dataReady = false;

	//------------------------------------------------------------------------

	@Override
	protected void OnInit() throws TradingException {
		// No-op: Strategy not yet available here
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


		// cpispec = value index 2
		String name = COTCompositeScore.findCotIndicatorName(CotSymbol, Period.toUpperCase());

		if(name != null) {
			map = COTCompositeScore.loadMap(name, 2);
		}
		dataReady = (map != null);

	}

	//------------------------------------------------------------------------

	@Override
	public double OnBlockEvaluate(int relativeShift) throws TradingException {
		lazyInit();

		if(!dataReady || Strategy == null) {
			return 0;
		}

		long barTime = Strategy.MarketData.Chart(0).Time(relativeShift + Shift);
		return map.getTime(barTime);
	}
}
