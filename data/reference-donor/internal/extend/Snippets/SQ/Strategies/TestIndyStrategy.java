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

import com.strategyquant.datalib.UpdateEventTypes;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.app.MainApp;

import SQ.Internal.Strategy;

/**
 * @author Mark Fric
 *
 */
public class TestIndyStrategy extends Strategy {
	
	private PrintWriter writer;
	private String fileName;
	private int eventType;
	private int dataIndex;
	private static DateTimeFormatter timeFormatter = DateTimeFormat.forPattern("yyyy.MM.dd;HH:mm");

	//------------------------------------------------------------------------
	//------------------------------------------------------------------------
	//------------------------------------------------------------------------

	public TestIndyStrategy() {
		this(UpdateEventTypes.BarOpen, 1);
	}
			
	//------------------------------------------------------------------------

	public TestIndyStrategy(int eventType, int dataIndex) {
		this.eventType = eventType;
		this.dataIndex = dataIndex;
	}
	
	//------------------------------------------------------------------------

	public double getIndyValue() throws Exception {
		return 0;
	}

	//------------------------------------------------------------------------

	@Override
	public void Initialize() throws Exception {
		 String filePath = MainApp.getDataPath() + "tests/tmp/"+fileName+".csv";
		 writer = new PrintWriter(new BufferedWriter(new FileWriter(new File(filePath), StandardCharsets.UTF_8)));
		 
		 this.setUpdateEventType(eventType);
	}

	//------------------------------------------------------------------------
	
	@Override
	public void OnBarUpdate() throws Exception {
		// line format: 2008.01.08;14:00;1.9749;660;1.97262
		String time = SQTime.toString(Time.get(dataIndex), timeFormatter);
		//Log.debug("XXXXXXXXXXXXXXXX  Computing value for "+time+", close: "+Close.get(1));
		
		double indyVal = getIndyValue();
		
		writer.println(time+";"+Close.get(dataIndex)+";"+Volume.get(dataIndex)+";"+indyVal);
	}

	//------------------------------------------------------------------------

	@Override
	public void Deinitialize() throws Exception {
		if(writer != null) {
			writer.close();
		}
	}

	//------------------------------------------------------------------------
	
	/**
	 * @param logFileName
	 */
	public void setLogName(String logFileName) {
		this.fileName = logFileName;
	}

}
