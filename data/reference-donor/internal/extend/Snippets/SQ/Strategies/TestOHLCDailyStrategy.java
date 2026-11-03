/*
 * Copyright (c) 2017-2018, StrategyQuant - All rights reserved.
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
package SQ.Strategies;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;

import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;

import SQ.Internal.Strategy;

import com.strategyquant.datalib.UpdateEventTypes;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.time.SQTimeOld;

public class TestOHLCDailyStrategy extends Strategy {
	
	private PrintWriter writer;
	private DateTimeFormatter timeFormatter = DateTimeFormat.forPattern("yyyy.MM.dd HH:mm:ss");
	private long startTime;
	
	//------------------------------------------------------------------------
	//------------------------------------------------------------------------
	//------------------------------------------------------------------------
	
	@Override
	public void Initialize() throws Exception {
		String filePath = MainApp.getDataPath() + "tests/tmp/STRATEGY_OHLCDaily.csv";
		writer = new PrintWriter(new BufferedWriter(new FileWriter(new File(filePath), StandardCharsets.UTF_8)));
		 
		SQTimeOld temp = new SQTimeOld(2008, 5, 20);
		startTime = temp.getMilis();
		
		this.setUpdateEventType(UpdateEventTypes.BarTick);
	}

	//------------------------------------------------------------------------

	@Override
	public void OnBarUpdate() throws Exception {
		if(Time.get(0) < startTime) {
			return;
		}
		
		String time = SQTime.toString(TimeCurrent(), timeFormatter);

		writer.println(time+";"+Open.get(0)+";"+High.get(0)+";"+Low.get(0)+";"+Close.get(0)+";"+Ask()+";"+Bid()+";"+
				OpenD.get(0)+";"+
				HighD.get(0)+";"+
				LowD.get(0)+";"+
				CloseD.get(0)+";"+
				OpenD.get(10)+";"+
				HighD.get(10)+";"+
				LowD.get(10)+";"+
				CloseD.get(10)+";"+
				OpenD.get(20)+";"+
				HighD.get(20)+";"+
				LowD.get(20)+";"+
				CloseD.get(20));
		
	}
	
	//------------------------------------------------------------------------

	@Override
	public void Deinitialize() throws Exception {
		if(writer != null) {
			writer.close();
		}
	}
}