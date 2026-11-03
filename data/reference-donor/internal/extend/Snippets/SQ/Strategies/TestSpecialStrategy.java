package SQ.Strategies;

import java.util.Map;

import com.strategyquant.datalib.UpdateEventTypes;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.OrderCloseTypes;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;

import SQ.Internal.Strategy;

public class TestSpecialStrategy  extends Strategy {
	
	private Map<Long, String[]> map;
	private ILiveOrder order;
	private boolean closed = true;
	private int bars;
	private long openTime;
	
	public TestSpecialStrategy(Map<Long, String[]> map) {
		this.map = map;
	}
	
	@Override
	public void Initialize() throws Exception {

	}

	@Override
	public void OnBarUpdate() throws Exception {
		if(UpdateEventType != UpdateEventTypes.BarOpen) {
			return;
		}
		
		ChartData chartData = MarketData.Chart(0);
		
		SQTimeOld time = new SQTimeOld(chartData.Time(0));
		if(this.map.containsKey(time.getMilis())) {
			String[] data = map.get(time.getMilis());
						
			double openPrice = order==null ? 0 : order.getOpenPrice();
			double acBalance = Trader.getAccountBalance();
			double acEquity = Trader.getAccountEquity(); //(chartData.Time(1) - openTime) / (3600 * 1000) > 24 && order != null && openTime != 0 ? Trader.getAccountEquity() + 0.5 : Trader.getAccountEquity();

			boolean closedF = data[2].equals("0");
			double openPriceF = Double.parseDouble(data[3]);
			double askF = Double.parseDouble(data[4]);
			double bidF = Double.parseDouble(data[5]);
			double acBalanceF = Double.parseDouble(data[6]);
			double acEquityF = Double.parseDouble(data[7]);			
			
			LiveOrderObj obj = (LiveOrderObj)order;

			System.out.println("Data file: "+time.toDateMinuteString()+" - " + (closedF ? "closed" : "open") +" - "+openPriceF+" - "+askF+" - "+bidF+" - "+acBalanceF+" - "+acEquityF);			
			System.out.println("Data SQ: "+time.toDateMinuteString()+" - "+ (closed ? "closed" : "open") +" - "+openPrice+" - "+chartData.Ask()+" - "+chartData.Bid()+" - "+acBalance+" - "+acEquity);
			
			if(SQUtils.round(acBalanceF, 2)!=SQUtils.round(acBalance, 2)) {
				throw new Exception("Incorrect account balance. "+time.toDateMinuteString()+" "+acBalance+" != "+acBalanceF);
			}
			
			if(SQUtils.round(acEquityF, 2)!=SQUtils.round(acEquity, 2)) {
				throw new Exception("Incorrect account equity. "+time.toDateMinuteString()+" "+acEquity+" != "+acEquityF);
			}

			if(closedF!=closed) {
				throw new Exception("Incorrect open type. "+time.toDateMinuteString()+" "+closed+" != "+closedF);
			}
		} else {
			throw new Exception("This is not good man. Missing data: "+time.toDateMinuteString());
		}
		
		time = new SQTimeOld(chartData.Time(1));
		
		bars++;
		
		if(order == null && time.getHour() == 8) {
			order = Trader.Buy(Symbol).setSize(0.1).setMagicNumber(1234).Send();
			openTime = chartData.Time(1);
			bars = 0;
			closed = false;
		}
		else if(order != null && bars == 8) {
			order.Close(OrderCloseTypes.Deleted);
			order = null;
			closed = true;
		}
	}

}

