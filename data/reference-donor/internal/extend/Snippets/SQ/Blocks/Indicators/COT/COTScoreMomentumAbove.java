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
 * COT Score Momentum Above (Strategies 10 + 37 combined).
 *
 * Checks whether the COTScore is improving (momentum positive) AND optionally
 * already above a minimum level. This combines Strategy 10 (pure momentum)
 * with Strategy 37 (level + momentum) via the optional LevelThreshold parameter.
 *
 * ScoreMomentum = COTScore_now - COTScore[MomentumLookback]
 * Condition: ScoreMomentum > MomentumThreshold
 *            AND (optionally) COTScore_now > LevelThreshold
 *
 * Set LevelThreshold=0 to use pure momentum only (Strategy 10).
 * Set LevelThreshold=0.40 to require both level + momentum (Strategy 37).
 *
 * Sources: Briese Movement Index [R3].
 */
@Help("COTScore Momentum Above threshold. Measures rate of change of COTScore. Set LevelThreshold=0 for pure momentum (Str10), or LevelThreshold>0 for level+momentum (Str37). (Strategy 10+37) — COT data provided by SpreadCharts.com")
@BuildingBlock(name="(COT17) Score Momentum Above", display="COTMomentumAbove(#CotSymbol#, mom>#MomentumThreshold#)", returnType = ReturnTypes.Boolean)
@SortOrder(1700)
@OppositeBlock(value="COTScoreMomentumBelow")
@ParameterSet(set="CotSymbol=AUTO")
@ForEngine("MT4,MT5,TS,MC,NT")
public class COTScoreMomentumAbove extends ConditionBlock {

	@Parameter(defaultValue="AUTO", name="COT Symbol")
	public String CotSymbol;

	@Parameter(defaultValue="0.15", minValue=0.05, maxValue=0.60, step=0.05, name="Momentum Threshold")
	public double MomentumThreshold;

	@Parameter(defaultValue="0.0", minValue=-0.50, maxValue=0.80, step=0.10, name="Min Level (0=disabled)")
	public double LevelThreshold;

	@Parameter(defaultValue="4", minValue=1, maxValue=12, step=1, name="Momentum Lookback")
	public int MomentumLookback;

	@Parameter
	public int Shift;

	private CustomDataIndyMap mapHedg52, mapHedg156, mapSpec52, mapSpec156;
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
		
					dataReady = (mapHedg52 != null && mapHedg156 != null && mapSpec52 != null && mapSpec156 != null);
				} catch(Exception e) {
					Log.error("COTScoreMomentumAbove OnInit error", e);
				}
	}

	private double calcScore(long barTime) {
		double h52 = mapHedg52.getTime(barTime);
		double h156 = mapHedg156.getTime(barTime);
		double s52 = mapSpec52.getTime(barTime);
		double s156 = mapSpec156.getTime(barTime);
		return ((h52 + h156) / 2.0) - ((s52 + s156) / 2.0);
	}

	@Override
	public boolean OnBlockEvaluate() throws TradingException {
		lazyInit();

		if(!dataReady) return false;

		long barTime     = Strategy.MarketData.Chart(0).Time(Shift);
		long prevBarTime = barTime - MomentumLookback * 7L * 24 * 3600 * 1000;

		double scoreNow  = calcScore(barTime);
		double scorePrev = calcScore(prevBarTime);
		double momentum  = scoreNow - scorePrev;

		// Momentum must exceed threshold
		if(momentum <= MomentumThreshold) return false;

		// Level filter (scoreNow must exceed LevelThreshold; at default 0.0 this means scoreNow > 0)
		if(scoreNow <= LevelThreshold) return false;

		return true;
	}
}
