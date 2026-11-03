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
 * COT Multi-Field Combo indicator — combines multiple COT fields into a single composite value.
 *
 * Default configuration (all four fields enabled):
 *   ComboScore = avg(cpihedg, cpispec_inverted, cpismall_inverted, ctispec_inverted)
 *
 * The idea: hedger bullishness PLUS speculator/small bearishness = strongest bullish setup.
 * Hedger fields contribute positively, speculator/small fields are inverted (1-value).
 *
 * Result range: 0 to 1.
 *     1 = all fields agree on extreme bullish (hedgers max long, specs/small max short)
 *     0 = all fields agree on extreme bearish
 *   0.5 = neutral
 */
@Help("COT Multi-Field Combo — combines multiple COT fields into a single composite score. " +
	"Default: avg(cpihedg, 1-cpispec, 1-cpismall, 1-ctispec). " +
	"Pavel's Euro (6E) recommendation: use cpihedg + cpispec + cpismall + ctispec together. " +
	"Range: 0 to 1. Value > 0.5 = bullish composite, < 0.5 = bearish composite. " +
	"Hedger fields contribute positively (high hedger = bullish). " +
	"Speculator and small trader fields are inverted (high spec = bearish, so inverted). " +
	"Works with any COT symbol. Best tested on FX (especially Euro 6E), commodities, and metals. " +
	"Use EnableField parameters to include/exclude specific COT fields from the composite. — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT) Multi-Field Combo", display="COTCombo(#CotSymbol#,#Period#)[#Shift#]", returnType = ReturnTypes.Number)
@Indicator(oscillator=true, middleValue=0.5, min=0, max=1, step=0.01)
@ParameterSet(set="CotSymbol=AUTO,Period=52w")
@ParameterSet(set="CotSymbol=AUTO,Period=156w")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTMultiFieldCombo extends IndicatorBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="156w", name="Period (52w or 156w)")
	public String Period;

	@Parameter(defaultValue="true", name="Use cpihedg (Hedger CPI)")
	public boolean UseCpihedg;

	@Parameter(defaultValue="true", name="Use cpispec (Speculator CPI, inverted)")
	public boolean UseCpispec;

	@Parameter(defaultValue="true", name="Use cpismall (Small Trader CPI, inverted)")
	public boolean UseCpismall;

	@Parameter(defaultValue="true", name="Use ctispec (Speculator CTI, inverted)")
	public boolean UseCtispec;

	@Output(name = "COTCombo", color = Colors.DodgerBlue)
	public com.strategyquant.datalib.DataSeries Value;

	private CustomDataIndyMap mapCpihedg, mapCpispec, mapCpismall, mapCtispec;
	private boolean dataReady = false;
	private int fieldCount = 0;

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
					if(name == null) {
						Log.error("COTMultiFieldCombo: No COT data found for {} {}", CotSymbol, Period);
						return;
					}
		
					fieldCount = 0;
					if(UseCpihedg)  { mapCpihedg  = COTCompositeScore.loadMap(name, 0); if(mapCpihedg  != null) fieldCount++; }
					if(UseCpispec)  { mapCpispec  = COTCompositeScore.loadMap(name, 2); if(mapCpispec  != null) fieldCount++; }
					if(UseCpismall) { mapCpismall = COTCompositeScore.loadMap(name, 4); if(mapCpismall != null) fieldCount++; }
					if(UseCtispec)  { mapCtispec  = COTCompositeScore.loadMap(name, 3); if(mapCtispec  != null) fieldCount++; }
		
					dataReady = (fieldCount > 0);
				} catch(Exception e) {
					Log.error("COTMultiFieldCombo OnInit error", e);
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
		double sum = 0;
		int count = 0;

		// Hedger CPI contributes positively (high = bullish)
		if(mapCpihedg != null) {
			sum += mapCpihedg.getTime(barTime);
			count++;
		}

		// Speculator CPI is inverted (high spec = bearish → invert for bullish composite)
		if(mapCpispec != null) {
			sum += (1.0 - mapCpispec.getTime(barTime));
			count++;
		}

		// Small trader CPI is inverted (same logic as specs)
		if(mapCpismall != null) {
			sum += (1.0 - mapCpismall.getTime(barTime));
			count++;
		}

		// Speculator CTI is inverted
		if(mapCtispec != null) {
			sum += (1.0 - mapCtispec.getTime(barTime));
			count++;
		}

		double combo = (count > 0) ? (sum / count) : 0.5;
		return combo;
	}
}
