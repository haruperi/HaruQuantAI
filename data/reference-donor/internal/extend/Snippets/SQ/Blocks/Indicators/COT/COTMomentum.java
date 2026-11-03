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

import SQ.Internal.IndicatorBlock;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.*;

import com.strategyquant.tradinglib.data.CustomDataIndyMap;

/**
 * COT Momentum — returns the change in a COT field over N periods.
 *
 * COTMomentum = CPI[0] - CPI[Lookback]
 *
 * This is designed as an ML feature: "is positioning accelerating?"
 * Positive momentum = group is increasing their net position.
 * Negative momentum = group is reducing their net position.
 *
 * Range: -1.0 to +1.0.
 */
@Help("COT Momentum — the change in a COT field over N bars. COTMomentum = CPI[now] - CPI[Lookback bars ago]. " +
	"Range: -1 to +1. Positive = positioning accelerating, negative = positioning decelerating. " +
	"FieldIndex: 0=cpihedg, 1=ctihedg, 2=cpispec, 3=ctispec, 4=cpismall. " +
	"Lookback: number of bars to measure change over (default 4 = ~1 month weekly). — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT) Momentum", display="COTMom(#CotSymbol#,#Period#,f#FieldIndex#,lb#Lookback#)[#Shift#]", returnType = ReturnTypes.Number)
@Indicator(oscillator=true, middleValue=0, min=-1, max=1, step=0.01)
@ParameterSet(set="CotSymbol=AUTO,Period=52w")
@ParameterSet(set="CotSymbol=AUTO,Period=156w")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTMomentum extends IndicatorBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="156w", name="Period (52w or 156w)")
	public String Period;

	@Parameter(defaultValue="0", minValue=0, maxValue=4, step=1, name="Field Index (0=cpihedg, 1=ctihedg, 2=cpispec, 3=ctispec, 4=cpismall)")
	public int FieldIndex;

	@Parameter(defaultValue="4", minValue=1, maxValue=52, step=1, name="Lookback (bars)")
	public int Lookback;

	@Output(name = "COTMom", color = Colors.DarkOrange)
	public com.strategyquant.datalib.DataSeries Value;

	private CustomDataIndyMap mapField;
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

		
				try {
					String name = COTCompositeScore.findCotIndicatorName(CotSymbol, Period.toUpperCase());
					if(name != null) {
						mapField = COTCompositeScore.loadMap(name, FieldIndex);
					}
					dataReady = (mapField != null);
				} catch(Exception e) {
					Log.error("COTMomentum OnInit error", e);
				}
	}

	//------------------------------------------------------------------------

	@Override
	public double OnBlockEvaluate(int relativeShift) throws TradingException {
		lazyInit();

		if(!dataReady || Strategy == null) {
			return 0;
		}

		long barTimeNow  = Strategy.MarketData.Chart(0).Time(relativeShift + Shift);
		long barTimePrev = Strategy.MarketData.Chart(0).Time(relativeShift + Shift + Lookback);

		double cotNow  = mapField.getTime(barTimeNow);
		double cotPrev = mapField.getTime(barTimePrev);

		double momentum = (cotNow - cotPrev);
		return momentum;
	}
}
