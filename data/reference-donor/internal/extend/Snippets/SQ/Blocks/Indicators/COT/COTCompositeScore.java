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
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Help;
import com.strategyquant.tradinglib.ForEngine;

import SQ.Internal.IndicatorBlock;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.tradinglib.data.CustomDataIndyCache;
import com.strategyquant.tradinglib.cot.CotManager;
import com.strategyquant.tradinglib.cot.CotSymbolResolver;
import com.strategyquant.tradinglib.data.CustomDataIndyMap;

import java.util.Collection;

/**
 * COT Composite Score indicator block.
 *
 * Compresses four CPI values into a single directional regime score:
 *   COTScore = avg(cpihedg52, cpihedg156) - avg(cpispec52, cpispec156)
 *
 * Range: -1.0 (max bearish divergence) to +1.0 (max bullish divergence).
 * Typical usage: allow long trades when COTScore > +0.60, short when < -0.60.
 */
@Help("COT Composite Score. Combines BOTH lookback windows into a single regime indicator: avg(HedgerCPI_52w, HedgerCPI_156w) - avg(SpecCPI_52w, SpecCPI_156w). " +
	"Range: roughly -1 to +1. " +
	"Value > 0 (positive): Hedgers are net bullish across both timeframes while speculators are net bearish — BULLISH regime. " +
	"Value = 0: No positioning edge — neutral regime. " +
	"Value < 0 (negative): Speculators are net bullish across both timeframes while hedgers are net bearish — BEARISH regime. " +
	"This is the most comprehensive single COT metric as it averages both short-term (52w) and long-term (156w) positioning. " +
	"Typical usage: allow LONG trades when COTScore > +0.30, SHORT trades when COTScore < -0.30. " +
	"Zero crossovers can signal regime changes. — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT) Composite Score", display="COTScore(#CotSymbol#)[#Shift#]", returnType = ReturnTypes.Number)
@Indicator(oscillator=true, middleValue=0, min=-1, max=1, step=0.05)
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTCompositeScore extends IndicatorBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Output(name = "COTScore", color = Colors.DeepSkyBlue)
	public com.strategyquant.datalib.DataSeries Value;

	// Cached data maps - loaded once in OnInit
	private CustomDataIndyMap mapHedg52;
	private CustomDataIndyMap mapHedg156;
	private CustomDataIndyMap mapSpec52;
	private CustomDataIndyMap mapSpec156;
	private boolean dataReady = false;

	//------------------------------------------------------------------------

	@Override
	protected void OnInit() throws TradingException {
		// Strategy is NOT yet available here (set after initialize())
		// Data loading is deferred to first OnBarUpdate call
	}

	//------------------------------------------------------------------------

	private boolean initialized = false;

	private void lazyInit() {
		if(initialized) return;
		initialized = true;

		if(Strategy == null) return;

		CotSymbol = resolveBlockSymbol(Strategy, CotSymbol);

		// Value index 0 = cpihedg for all COT indicators
		int hedgIdx = 0;
		// Value index 2 = cpispec for all COT indicators
		int specIdx = 2;

		// Find the 52w and 156w indicators for this symbol
		String name52  = findCotIndicatorName(CotSymbol, "52W");
		String name156 = findCotIndicatorName(CotSymbol, "156W");

		if(name52 != null) {
			mapHedg52 = loadMap(name52, hedgIdx);
			mapSpec52 = loadMap(name52, specIdx);
		}

		if(name156 != null) {
			mapHedg156 = loadMap(name156, hedgIdx);
			mapSpec156 = loadMap(name156, specIdx);
		}

		dataReady = (mapHedg52 != null && mapHedg156 != null && mapSpec52 != null && mapSpec156 != null);

		if(!dataReady) {
			Log.warn("COTCompositeScore: Could not load all data maps for symbol {}. " +
			         "52w={}, 156w={}", CotSymbol, name52, name156);
		}
	}

	//------------------------------------------------------------------------

	@Override
	protected void OnBarUpdate() throws TradingException {
		// Not used - OnBlockEvaluate is overridden
	}

	//------------------------------------------------------------------------

	@Override
	public double OnBlockEvaluate(int relativeShift) throws TradingException {
		lazyInit();

		if(!dataReady || Strategy == null) {
			return 0;
		}

		long barTime = Strategy.MarketData.Chart(0).Time(relativeShift + Shift);

		double hedg52  = mapHedg52.getTime(barTime);
		double hedg156 = mapHedg156.getTime(barTime);
		double spec52  = mapSpec52.getTime(barTime);
		double spec156 = mapSpec156.getTime(barTime);

		// COTScore = avg(hedger CPIs) - avg(speculator CPIs)
		double score = ((hedg52 + hedg156) / 2.0) - ((spec52 + spec156) / 2.0);

		return score;
	}

	//------------------------------------------------------------------------

	/**
	 * Finds the registered COT indicator name for a given symbol and period.
	 * COT indicators are named like "COT 6E 52W CME Euro FX".
	 * This method searches all registered custom data indicators for a match.
	 */
	static String findCotIndicatorName(String symbol, String period) {
		try {
			String prefix = "COT " + symbol + " " + period;
			Collection<CustomDataInfo> allData = CustomDataManager.list();
			for(CustomDataInfo info : allData) {
				if(info.name != null && info.name.startsWith(prefix)) {
					return info.name;
				}
			}
		} catch(Exception e) {
			Log.error("COT findCotIndicatorName: EXCEPTION", e);
		}
		return null;
	}

	/**
	 * Loads a CustomDataIndyMap directly from the cache by indicator name and value index.
	 */
	static CustomDataIndyMap loadMap(String indyName, int valueIndex) {
		try {
			CustomDataInfo dataInfo = CustomDataManager.getDataInfo(indyName);
			if(dataInfo == null) return null;

			// Use reflection-free approach: build the cache key and load
			long key = SQUtils.longHashCode(indyName) + valueIndex;

			// Try to get from cache first
			org.jdom2.Element el = new org.jdom2.Element("Item");
			el.setAttribute("key", "CDataIndy_" + indyName);
			org.jdom2.Element elParam = new org.jdom2.Element("Param");
			elParam.setAttribute("key", "#Value#");
			elParam.setAttribute("type", "int");
			elParam.setText(Integer.toString(valueIndex));
			el.addContent(elParam);

			return CustomDataIndyCache.getMapForIndy(el);
		} catch(Exception e) {
			Log.error("COT loadMap: EXCEPTION for '{}'", indyName, e);
			return null;
		}
	}

	//------------------------------------------------------------------------
	// COT Symbol Auto-Resolver
	//------------------------------------------------------------------------

	// The COT market of a chart symbol is fixed by its instrument (Data Manager > Instruments > COT), nothing is
	// guessed from the symbol name. A missing COT market is an error the user has to fix, so it throws.
	public static String resolveCotSymbol(String instrumentSymbol) {
		return CotManager.getInstance().getCotSymbol(instrumentSymbol);
	}

	// Random COT market out of the downloaded COT data. Used when CotSymbol is set to "RAND".
	public static String randomCotSymbol() {
		return CotSymbolResolver.randomCotSymbol(null);
	}

	// the random COT market picked for a strategy instance: all its RAND blocks read the same one, the one
	// written into its XML
	private static final java.util.Map<Object, String> randomSymbols = new java.util.WeakHashMap<Object, String>();

	// Turns the CotSymbol parameter of a block into a real COT market: AUTO is the COT market of the strategy's
	// instrument, RAND a random downloaded one, anything else is used as typed. A resolved AUTO or RAND is
	// written into the strategy XML so later backtests and the exports see the real symbol.
	public static String resolveBlockSymbol(StrategyBase strategy, String cotSymbol) {
		if("AUTO".equalsIgnoreCase(cotSymbol)) {
			String resolved = resolveCotSymbol(strategy.getSymbol());
			persistCotSymbolToXml(strategy, "AUTO", resolved);
			return resolved;
		}
		if("RAND".equalsIgnoreCase(cotSymbol)) {
			synchronized(randomSymbols) {
				String resolved = randomSymbols.get(strategy);
				if(resolved == null) {
					resolved = randomCotSymbol();
					randomSymbols.put(strategy, resolved);
					persistCotSymbolToXml(strategy, "RAND", resolved);
				}
				return resolved;
			}
		}
		return cotSymbol;
	}

	// Writes the resolved COT symbol into the strategy XML in place of the given placeholder (AUTO / RAND), so
	// later backtests and the exports see the real symbol (e.g. "6E").
	public static void persistCotSymbolToXml(Object strategy, String placeholder, String resolved) {
		if(strategy == null || resolved == null) return;
		try {
			// Call strategy.getStrategyXml() via reflection
			java.lang.reflect.Method getXml = strategy.getClass().getMethod("getStrategyXml");
			Object root = getXml.invoke(strategy);
			if(root == null) return;

			updateCotSymbolParams(root, placeholder, resolved);
		} catch(Exception e) {
			// silently ignore
		}
	}

	// Writes a value into the EMPTY #CotSymbol# params of the given block type only (VixProxy blocks
	// have no AUTO, the Builder leaves their free-text symbol empty); other blocks are not touched.
	public static void persistEmptyCotSymbolToXml(Object strategy, String blockKey, String value) {
		if(strategy == null || blockKey == null || value == null) return;
		try {
			java.lang.reflect.Method getXml = strategy.getClass().getMethod("getStrategyXml");
			Object root = getXml.invoke(strategy);
			if(root == null) return;

			updateEmptyCotSymbolParams(root, blockKey, value, false);
		} catch(Exception e) {
			// silently ignore
		}
	}

	private static int updateEmptyCotSymbolParams(Object element, String blockKey, String value, boolean insideBlock) throws Exception {
		int count = 0;
		String name = (String) element.getClass().getMethod("getName").invoke(element);
		String key = (String) element.getClass().getMethod("getAttributeValue", String.class).invoke(element, "key");
		if(("Item".equals(name) || "Block".equals(name)) && key != null) {
			insideBlock = blockKey.equals(key);
		}
		if(insideBlock && "Param".equals(name) && ("CotSymbol".equals(key) || "#CotSymbol#".equals(key))) {
			String currentVal = (String) element.getClass().getMethod("getTextTrim").invoke(element);
			if(currentVal == null || currentVal.isEmpty()) {
				element.getClass().getMethod("setText", String.class).invoke(element, value);
				count++;
			}
		}
		java.util.List<?> children = (java.util.List<?>) element.getClass().getMethod("getChildren").invoke(element);
		for(Object child : children) {
			count += updateEmptyCotSymbolParams(child, blockKey, value, insideBlock);
		}
		return count;
	}

	@SuppressWarnings("unchecked")
	private static int updateCotSymbolParams(Object element, String placeholder, String resolved) throws Exception {
		int count = 0;
		// element.getName()
		String name = (String) element.getClass().getMethod("getName").invoke(element);
		if("Param".equals(name)) {
			// element.getAttributeValue("key")
			String key = (String) element.getClass().getMethod("getAttributeValue", String.class).invoke(element, "key");
			if("CotSymbol".equals(key) || "#CotSymbol#".equals(key)) {
				// element.getTextTrim()
				String currentVal = (String) element.getClass().getMethod("getTextTrim").invoke(element);
				if(placeholder.equalsIgnoreCase(currentVal)) {
					// element.setText(resolved)
					element.getClass().getMethod("setText", String.class).invoke(element, resolved);
					count++;
				}
			}
		}
		// element.getChildren()
		java.util.List<?> children = (java.util.List<?>) element.getClass().getMethod("getChildren").invoke(element);
		for(Object child : children) {
			count += updateCotSymbolParams(child, placeholder, resolved);
		}
		return count;
	}
}
