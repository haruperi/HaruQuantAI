/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataSeries
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.bartype.BarType
 *  com.strategyquant.datalib.bartype.BarTypeFactory
 *  com.strategyquant.datalib.bartype.BarTypeStatus
 *  com.strategyquant.datalib.bartype.impl.FuturesTimeBar
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.dataseries.ComputedDataSeries
 *  com.strategyquant.datalib.dataseries.MedianDataSeries
 *  com.strategyquant.datalib.dataseries.TimeDataSeries
 *  com.strategyquant.datalib.dataseries.TypicalDataSeries
 *  com.strategyquant.datalib.dataseries.WeightedDataSeries
 *  com.strategyquant.datalib.session.Session
 *  com.strategyquant.datalib.session.SessionManager
 *  com.strategyquant.datalib.session.SessionStatus
 *  com.strategyquant.lib.SQTime
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataSeries;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.bartype.BarType;
import com.strategyquant.datalib.bartype.BarTypeFactory;
import com.strategyquant.datalib.bartype.BarTypeStatus;
import com.strategyquant.datalib.bartype.impl.FuturesTimeBar;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.dataseries.ComputedDataSeries;
import com.strategyquant.datalib.dataseries.MedianDataSeries;
import com.strategyquant.datalib.dataseries.TimeDataSeries;
import com.strategyquant.datalib.dataseries.TypicalDataSeries;
import com.strategyquant.datalib.dataseries.WeightedDataSeries;
import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.datalib.session.SessionStatus;
import com.strategyquant.lib.SQTime;
import com.strategyquant.tradinglib.debug.Debugger;
import com.strategyquant.tradinglib.strategy.MarketData;
import java.io.Serializable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ChartData
extends Debugger
implements Serializable {
    public static final Logger Log = LoggerFactory.getLogger((String)"ChartData");
    public static final int ChartTF_D1 = 1;
    public static final int ChartTF_W1 = 2;
    public static final int ChartTF_M1 = 3;
    public TimeDataSeries Time;
    public DataSeries Open;
    public DataSeries High;
    public DataSeries Low;
    public DataSeries Close;
    public ComputedDataSeries Median;
    public ComputedDataSeries Typical;
    public ComputedDataSeries Weighted;
    protected TimeDataSeries TimeD;
    protected DataSeries OpenD;
    protected DataSeries HighD;
    protected DataSeries LowD;
    protected DataSeries CloseD;
    protected TimeDataSeries TimeW;
    protected DataSeries OpenW;
    protected DataSeries HighW;
    protected DataSeries LowW;
    protected DataSeries CloseW;
    protected TimeDataSeries TimeM;
    protected DataSeries OpenM;
    protected DataSeries HighM;
    protected DataSeries LowM;
    protected DataSeries CloseM;
    private double dailyHigh;
    private double dailyLow;
    private double weeklyHigh;
    private double weeklyLow;
    private double monthlyHigh;
    private double monthlyLow;
    public DataSeries Volume;
    public MarketData MarketData;
    public String Connection;
    public String Symbol;
    public String Instrument;
    public String Timeframe;
    protected String session;
    protected int requestedEventType = 4;
    protected int connectionHash;
    protected int symbolHash;
    private boolean updated;
    protected BarType barType;
    protected InstrumentInfo SymbolInfo;
    private final BarTypeStatus barTypeStatus = new BarTypeStatus();
    private long TimeCurrent;
    private double Bid;
    private double Ask;
    protected ChartDef chartDef;
    public int EventType = 0;
    private ChartData connectedObject = null;
    private double barHigh;
    private double barLow;
    private double barVolume;
    private long nextDayTick = Long.MIN_VALUE;
    private long nextWeekTick = Long.MIN_VALUE;
    private long nextMonthTick = Long.MIN_VALUE;
    private long currentBarTime = Long.MIN_VALUE;
    private long currentDayEnd = Long.MIN_VALUE;
    private long nextBarTime = Long.MIN_VALUE;
    private int nextBarIndex = -1;
    protected boolean hasOnTickRule = true;
    protected boolean hasDailyDataBlock = true;
    protected boolean hasWeeklyDataBlock = true;
    protected boolean hasMonthlyDataBlock = true;
    private int hashCode = -1;
    private int currentBar = -1;
    protected int serieIndex = 0;
    private int chartTF = 0;
    private Session sessionDaily;
    private Session sessionWeekly;
    private Session sessionMonthly;
    private SessionStatus sessionStatus = new SessionStatus();
    private boolean useSessionWhenComputingDWM = false;
    private int indyStartingBar = 0;
    private TickEvent backupTick = new TickEvent();

    public ChartData() {
        boolean bl = true;
    }

    public ChartData(String string, TimeDataSeries timeDataSeries, DataSeries dataSeries, DataSeries dataSeries2, DataSeries dataSeries3, DataSeries dataSeries4, DataSeries dataSeries5, TimeDataSeries timeDataSeries2, DataSeries dataSeries6, DataSeries dataSeries7, DataSeries dataSeries8, DataSeries dataSeries9, TimeDataSeries timeDataSeries3, DataSeries dataSeries10, DataSeries dataSeries11, DataSeries dataSeries12, DataSeries dataSeries13, TimeDataSeries timeDataSeries4, DataSeries dataSeries14, DataSeries dataSeries15, DataSeries dataSeries16, DataSeries dataSeries17) {
        this.Timeframe = string;
        this.Time = timeDataSeries;
        if (this.Time != null) {
            this.Time.setName("Time");
        }
        this.Open = dataSeries;
        if (this.Open != null) {
            this.Open.setName("Open");
        }
        this.High = dataSeries2;
        if (this.High != null) {
            this.High.setName("High");
        }
        this.Low = dataSeries3;
        if (this.Low != null) {
            this.Low.setName("Low");
        }
        this.Close = dataSeries4;
        if (this.Close != null) {
            this.Close.setName("Close");
        }
        this.Volume = dataSeries5;
        if (this.Volume != null) {
            this.Volume.setName("Volume");
        }
        this.TimeD = timeDataSeries2;
        if (this.TimeD != null) {
            this.TimeD.setName("TimeD");
        }
        this.OpenD = dataSeries6;
        if (this.OpenD != null) {
            this.OpenD.setName("OpenD");
        }
        this.HighD = dataSeries7;
        if (this.HighD != null) {
            this.HighD.setName("HighD");
        }
        this.LowD = dataSeries8;
        if (this.LowD != null) {
            this.LowD.setName("LowD");
        }
        this.CloseD = dataSeries9;
        if (this.CloseD != null) {
            this.CloseD.setName("CloseD");
        }
        this.TimeW = timeDataSeries3;
        if (this.TimeW != null) {
            this.TimeW.setName("TimeW");
        }
        this.OpenW = dataSeries10;
        if (this.OpenW != null) {
            this.OpenW.setName("OpenW");
        }
        this.HighW = dataSeries11;
        if (this.HighW != null) {
            this.HighW.setName("HighW");
        }
        this.LowW = dataSeries12;
        if (this.LowW != null) {
            this.LowW.setName("LowW");
        }
        this.CloseW = dataSeries13;
        if (this.CloseW != null) {
            this.CloseW.setName("CloseW");
        }
        this.TimeM = timeDataSeries4;
        if (this.TimeM != null) {
            this.TimeM.setName("TimeM");
        }
        this.OpenM = dataSeries14;
        if (this.OpenM != null) {
            this.OpenM.setName("OpenM");
        }
        this.HighM = dataSeries15;
        if (this.HighM != null) {
            this.HighM.setName("HighM");
        }
        this.LowM = dataSeries16;
        if (this.LowM != null) {
            this.LowM.setName("LowM");
        }
        this.CloseM = dataSeries17;
        if (this.CloseM != null) {
            this.CloseM.setName("CloseM");
        }
        this.initializeComputedDataSeries();
    }

    public ChartData(MarketData marketData, ChartDef chartDef, int n, int n2) throws Exception {
        if (marketData == null && chartDef == null) {
            return;
        }
        this.chartDef = chartDef;
        this.serieIndex = n;
        this.MarketData = marketData;
        this.Connection = chartDef.getConnectionName();
        this.Symbol = chartDef.getSymbol();
        this.Instrument = chartDef.getInstrument();
        this.connectionHash = chartDef.getConnectionHash();
        this.symbolHash = chartDef.getSymbolHash();
        this.Timeframe = chartDef.getTimeframe();
        this.session = chartDef.getSession();
        this.Time = new TimeDataSeries();
        this.Time.setName("Time", chartDef);
        if (marketData != null) {
            this.Time.setIndyStartingBar(marketData.getIndyStartingBar());
        }
        this.Open = new DataSeries();
        this.Open.setName("Open", chartDef);
        if (marketData != null) {
            this.Open.setIndyStartingBar(marketData.getIndyStartingBar());
        }
        this.High = new DataSeries();
        this.High.setName("High", chartDef);
        if (marketData != null) {
            this.High.setIndyStartingBar(marketData.getIndyStartingBar());
        }
        this.Low = new DataSeries();
        this.Low.setName("Low", chartDef);
        if (marketData != null) {
            this.Low.setIndyStartingBar(marketData.getIndyStartingBar());
        }
        this.Close = new DataSeries();
        this.Close.setName("Close", chartDef);
        if (marketData != null) {
            this.Close.setIndyStartingBar(marketData.getIndyStartingBar());
        }
        this.Volume = new DataSeries();
        this.Volume.setName("Volume", chartDef);
        if (marketData != null) {
            this.Volume.setIndyStartingBar(marketData.getIndyStartingBar());
        }
        this.SymbolInfo = chartDef.getSymbolInfo();
        this.barType = BarTypeFactory.getBarType((String)this.Timeframe, (int)chartDef.getBarTimeType()).clone();
        String string = null;
        try {
            string = DataManager.getDataInfo((String)"History", (String)this.Symbol).timeframe;
        }
        catch (Exception exception) {
            Log.error("Cannot get original data timeframe");
        }
        if (this.barType instanceof FuturesTimeBar) {
            if (n2 == -659455871 || n2 == 395961824 || n2 == 1441180233) {
                ((FuturesTimeBar)this.barType).MetaTraderEngineUsed = true;
            } else if (string != null && string.equals(this.Timeframe)) {
                ((FuturesTimeBar)this.barType).LoadAsIs = true;
            }
        }
        if (this.usesSameDailyDataSeries()) {
            this.TimeD = this.Time;
            this.OpenD = this.Open;
            this.HighD = this.High;
            this.LowD = this.Low;
            this.CloseD = this.Close;
            this.TimeW = this.Time;
            this.OpenW = this.Open;
            this.HighW = this.High;
            this.LowW = this.Low;
            this.CloseW = this.Close;
            this.TimeM = this.Time;
            this.OpenM = this.Open;
            this.HighM = this.High;
            this.LowM = this.Low;
            this.CloseM = this.Close;
        } else {
            this.TimeD = null;
            this.OpenD = null;
            this.HighD = null;
            this.LowD = null;
            this.CloseD = null;
            this.TimeW = null;
            this.OpenW = null;
            this.HighW = null;
            this.LowW = null;
            this.CloseW = null;
            this.TimeM = null;
            this.OpenM = null;
            this.HighM = null;
            this.LowM = null;
            this.CloseM = null;
        }
        this.initializeComputedDataSeries();
        if (marketData != null) {
            this.setIndyStartingBar(marketData.getIndyStartingBar());
        }
    }

    protected boolean usesSameDailyDataSeries() {
        return this.serieIndex > 0 && this.chartDef.getBarTimeType() == 2;
    }

    public int chartHashCode() {
        if (this.hashCode == -1) {
            this.hashCode = this.hashCode();
        }
        return this.hashCode;
    }

    protected void initializeFromMarketData(MarketData marketData) {
        this.MarketData = marketData;
        this.Connection = this.MarketData.Chart((int)0).Connection;
        this.Symbol = this.MarketData.Chart((int)0).Symbol;
        this.connectionHash = this.MarketData.Chart(0).getConnectionHash();
        this.symbolHash = this.MarketData.Chart(0).getSymbolHash();
        this.Timeframe = this.MarketData.Chart((int)0).Timeframe;
        this.Time = this.MarketData.Chart((int)0).Time;
        this.Time.setName("Time");
        this.Open = this.MarketData.Chart((int)0).Open;
        this.Open.setName("Open");
        this.High = this.MarketData.Chart((int)0).High;
        this.High.setName("High");
        this.Low = this.MarketData.Chart((int)0).Low;
        this.Low.setName("Low");
        this.Close = this.MarketData.Chart((int)0).Close;
        this.Close.setName("Close");
        this.Volume = this.MarketData.Chart((int)0).Volume;
        this.Volume.setName("Volume");
        this.TimeD = this.MarketData.Chart((int)0).TimeD;
        this.OpenD = this.MarketData.Chart((int)0).OpenD;
        this.HighD = this.MarketData.Chart((int)0).HighD;
        this.LowD = this.MarketData.Chart((int)0).LowD;
        this.CloseD = this.MarketData.Chart((int)0).CloseD;
        this.TimeW = this.MarketData.Chart((int)0).TimeW;
        this.OpenW = this.MarketData.Chart((int)0).OpenW;
        this.HighW = this.MarketData.Chart((int)0).HighW;
        this.LowW = this.MarketData.Chart((int)0).LowW;
        this.CloseW = this.MarketData.Chart((int)0).CloseW;
        this.TimeM = this.MarketData.Chart((int)0).TimeM;
        this.OpenM = this.MarketData.Chart((int)0).OpenM;
        this.HighM = this.MarketData.Chart((int)0).HighM;
        this.LowM = this.MarketData.Chart((int)0).LowM;
        this.CloseM = this.MarketData.Chart((int)0).CloseM;
        this.initializeComputedDataSeries();
        this.SymbolInfo = this.MarketData.Chart((int)0).SymbolInfo;
        this.barType = this.MarketData.Chart((int)0).barType;
        marketData.Chart(0).addConnectedObject(this);
        this.setIndyStartingBar(marketData.getIndyStartingBar());
    }

    protected void initializeComputedDataSeries() {
        this.Median = new MedianDataSeries(this.Open, this.High, this.Low, this.Close, this.Volume);
        this.Median.setName("Median", this.chartDef);
        this.Typical = new TypicalDataSeries(this.Open, this.High, this.Low, this.Close, this.Volume);
        this.Typical.setName("Typical", this.chartDef);
        this.Weighted = new WeightedDataSeries(this.Open, this.High, this.Low, this.Close, this.Volume);
        this.Weighted.setName("Weighted", this.chartDef);
    }

    private void addConnectedObject(ChartData chartData) {
        if (this.connectedObject != null) {
            throw new IllegalArgumentException("Connected object must be null!");
        }
        this.connectedObject = chartData;
    }

    public long TimeCurrent() throws TradingException {
        return this.TimeCurrent;
    }

    public long Time(int n) throws TradingException {
        return this.Time.get(n);
    }

    public long Time() throws TradingException {
        return this.Time(0);
    }

    public long Time(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).Time(n2);
    }

    public long TimeD(int n) throws TradingException {
        if (this.TimeD == null) {
            return 0L;
        }
        return this.TimeD.get(n);
    }

    public long TimeW(int n) throws TradingException {
        if (this.TimeW == null) {
            return 0L;
        }
        return this.TimeW.get(n);
    }

    public long TimeM(int n) throws TradingException {
        if (this.TimeM == null) {
            return 0L;
        }
        return this.TimeM.get(n);
    }

    public double Ask() throws TradingException {
        return this.Ask != 0.0 ? this.Ask : this.Close(0);
    }

    public double Bid() throws TradingException {
        return this.Bid != 0.0 ? this.Bid : this.Close(0);
    }

    public double Open(int n) throws TradingException {
        return this.Open.get(n);
    }

    public double Open(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).Open(n2);
    }

    public double OpenD(int n) throws TradingException {
        if (this.OpenD == null) {
            return 0.0;
        }
        return this.OpenD.get(n);
    }

    public double OpenD(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).OpenD(n2);
    }

    public double OpenW(int n) throws TradingException {
        if (this.OpenW == null) {
            return 0.0;
        }
        return this.OpenW.get(n);
    }

    public double OpenW(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).OpenW(n2);
    }

    public double OpenM(int n) throws TradingException {
        if (this.OpenM == null) {
            return 0.0;
        }
        return this.OpenM.get(n);
    }

    public double OpenM(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).OpenM(n2);
    }

    public double Close(int n) throws TradingException {
        return this.Close.get(n);
    }

    public double Close(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).Close(n2);
    }

    public double CloseD(int n) throws TradingException {
        if (this.CloseD == null) {
            return 0.0;
        }
        return this.CloseD.get(n);
    }

    public double CloseD(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).CloseD(n2);
    }

    public double CloseW(int n) throws TradingException {
        if (this.CloseW == null) {
            return 0.0;
        }
        return this.CloseW.get(n);
    }

    public double CloseW(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).CloseW(n2);
    }

    public double CloseM(int n) throws TradingException {
        if (this.CloseM == null) {
            return 0.0;
        }
        return this.CloseM.get(n);
    }

    public double CloseM(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).CloseM(n2);
    }

    public double High(int n) throws TradingException {
        return this.High.get(n);
    }

    public double High(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).High(n2);
    }

    public double HighD(int n) throws TradingException {
        if (this.HighD == null) {
            return 0.0;
        }
        return this.HighD.get(n);
    }

    public double HighD(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).HighD(n2);
    }

    public double HighW(int n) throws TradingException {
        if (this.HighW == null) {
            return 0.0;
        }
        return this.HighW.get(n);
    }

    public double HighW(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).HighW(n2);
    }

    public double HighM(int n) throws TradingException {
        if (this.HighM == null) {
            return 0.0;
        }
        return this.HighM.get(n);
    }

    public double HighM(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).HighM(n2);
    }

    public double Low(int n) throws TradingException {
        return this.Low.get(n);
    }

    public double Low(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).Low(n2);
    }

    public double LowD(int n) throws TradingException {
        if (this.LowD == null) {
            return 0.0;
        }
        return this.LowD.get(n);
    }

    public double LowD(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).LowD(n2);
    }

    public double LowW(int n) throws TradingException {
        if (this.LowW == null) {
            return 0.0;
        }
        return this.LowW.get(n);
    }

    public double LowW(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).LowW(n2);
    }

    public double LowM(int n) throws TradingException {
        if (this.LowM == null) {
            return 0.0;
        }
        return this.LowM.get(n);
    }

    public double LowM(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).LowM(n2);
    }

    public double Volume(int n) throws TradingException {
        return this.Volume.get(n);
    }

    public double Openint(int n) throws TradingException {
        return 0.0;
    }

    public double Volume(int n, int n2) throws TradingException {
        return this.MarketData.Chart(n).Volume(n2);
    }

    public double Median(int n) throws TradingException {
        return this.Median.get(n);
    }

    public double Typical(int n) throws TradingException {
        return this.Typical.get(n);
    }

    public int Bars() {
        return this.Time.size();
    }

    public int Bars(int n) {
        return this.MarketData.Chart((int)n).Time.size();
    }

    public int getConnectionHash() {
        return this.connectionHash;
    }

    public int getSymbolHash() {
        return this.symbolHash;
    }

    public String getSymbol() {
        return this.Symbol;
    }

    public void setSymbol(String string) {
        this.Symbol = string;
        this.symbolHash = string.hashCode();
    }

    public String getConnectionName() {
        return this.Connection;
    }

    final void setUpdated(boolean bl) {
        this.updated = bl;
    }

    public boolean isUpdated() {
        return this.updated;
    }

    public void processTick(TickEvent tickEvent, int n, int n2) throws Exception {
        if (n == 3) {
            this.updated = false;
            this.EventType = 1;
        }
        if (this.connectionHash != tickEvent.getConnectionHash()) {
            return;
        }
        if (this.symbolHash != tickEvent.getSymbolHash()) {
            return;
        }
        if (n == 3) {
            this.barType.processTick(tickEvent, this.barTypeStatus, n2);
        }
        if (this.barTypeStatus.status == 0) {
            return;
        }
        if (this.barTypeStatus.status == 2) {
            if (n == 3) {
                this.updateBarData(tickEvent, true);
                this.setUpdated(true);
            }
        } else if (n == 3) {
            if (this.Time.size() > 0) {
                this.EventType = 3;
                this.setUpdated(true);
            }
        } else {
            this.createBarData(tickEvent, this.barTypeStatus.barTime);
            this.EventType = 2;
            this.setUpdated(true);
        }
        boolean bl = this.useSessionWhenComputingDWM = !"No Session".equals(this.chartDef.getSession());
        if (this.hasDailyDataBlock) {
            this.processDailyData(tickEvent);
        }
        if (this.hasWeeklyDataBlock) {
            this.processWeeklyData(tickEvent);
        }
        if (this.hasMonthlyDataBlock) {
            this.processMonthlyData(tickEvent);
        }
    }

    public void findTickInData(TickEvent tickEvent, int n, boolean bl, boolean bl2, int n2) throws Exception {
        if (!bl || n == 3) {
            this.updated = false;
            this.EventType = 1;
        }
        if (this.connectionHash != tickEvent.getConnectionHash()) {
            return;
        }
        if (this.symbolHash != tickEvent.getSymbolHash()) {
            return;
        }
        if (this.currentBarTime == Long.MIN_VALUE || this.nextBarTime > Long.MIN_VALUE && tickEvent.getTime() >= this.nextBarTime && this.nextBarTime > this.currentBarTime) {
            if (n == 3) {
                if (!bl) {
                    return;
                }
                if (this.currentBarTime > Long.MIN_VALUE) {
                    this.EventType = 3;
                    this.setUpdated(true);
                }
            } else {
                int n3;
                if (this.currentBarTime == Long.MIN_VALUE) {
                    n3 = this.findShift(tickEvent.getTime());
                    if (n3 == -1) {
                        throw new DataException(5, "Cannot find bar corresponding to tick");
                    }
                } else {
                    n3 = this.Time.getShift() - 1;
                }
                this.moveDataSeriesShift(n3);
                if (bl2) {
                    this.updateBarData(tickEvent, true);
                    this.callDataChangeListeners();
                }
                this.EventType = 2;
                this.setUpdated(true);
            }
        } else if (!(tickEvent.getTime() < this.currentBarTime || bl && n != 3)) {
            if (this.hasOnTickRule && n2 == 0) {
                this.updateBarData(tickEvent, true);
            }
            this.setUpdated(true);
        }
        this.useSessionWhenComputingDWM = !"No Session".equals(this.chartDef.getSession());
        this.backupTick.copyValues(tickEvent);
        if (this.hasDailyDataBlock && n != 3 && (this.serieIndex == 0 || this.barType.getBarTimeType() != 2)) {
            this.processDailyData(tickEvent);
        }
        if (this.hasWeeklyDataBlock && n != 3 && (this.serieIndex == 0 || this.barType.getBarTimeType() != 2)) {
            this.processWeeklyData(tickEvent);
        }
        if (this.hasMonthlyDataBlock && n != 3 && (this.serieIndex == 0 || this.barType.getBarTimeType() != 2)) {
            this.processMonthlyData(tickEvent);
        }
        tickEvent.copyValues(this.backupTick);
    }

    public boolean isNextDay(TickEvent tickEvent) {
        if (this.currentBarTime == Long.MIN_VALUE) {
            return true;
        }
        return tickEvent.getTime() > this.currentDayEnd;
    }

    public void findTickInDataComplete(TickEvent tickEvent, int n) throws Exception {
        if (n == 3) {
            this.updated = false;
            this.EventType = 1;
        }
        if (this.connectionHash != tickEvent.getConnectionHash()) {
            return;
        }
        if (this.symbolHash != tickEvent.getSymbolHash()) {
            return;
        }
        if (this.currentBarTime == Long.MIN_VALUE || this.nextBarTime > Long.MIN_VALUE && tickEvent.getTime() >= this.nextBarTime && this.nextBarTime > this.currentBarTime) {
            if (n == 3) {
                if (this.currentBarTime > Long.MIN_VALUE) {
                    this.EventType = 3;
                    this.setUpdated(true);
                }
            } else {
                int n2;
                if (this.currentBarTime == Long.MIN_VALUE) {
                    n2 = this.findShift(tickEvent.getTime());
                    if (n2 == -1) {
                        throw new DataException(5, "Cannot find bar corresponding to tick");
                    }
                } else {
                    n2 = this.Time.getShift() - 1;
                }
                this.moveDataSeriesShift(n2);
                this.updateBarData(tickEvent, true);
                this.callDataChangeListeners();
            }
        } else {
            if (tickEvent.getTime() < this.currentBarTime) {
                throw new DataException(5, "Bar time doesn't correspond to tick");
            }
            if (n == 3) {
                this.updateBarData(tickEvent, true);
                this.setUpdated(true);
            }
        }
        this.processDailyData(tickEvent);
    }

    private int findShift(long l) throws DataException, TradingException {
        int n = this.Time.getShift();
        int n2 = -1;
        for (int i = 1; i < 100; ++i) {
            long l2 = this.Time.get(0);
            this.Time.setShift(n - i);
            long l3 = this.Time.get(0);
            if (l < l2 || l >= l3) continue;
            n2 = n - i + 1;
            break;
        }
        if (n2 == -1) {
            this.Time.setShift(n);
            if (l <= this.Time.get(0)) {
                return n;
            }
            throw new DataException(5, "Cannot find bar corresponding to tick");
        }
        return n2;
    }

    private void moveDataSeriesShift(int n) throws TradingException {
        if (n == this.nextBarIndex) {
            this.currentBarTime = this.nextBarTime;
        } else {
            this.Time.setShift(n);
            this.currentBarTime = this.Time.get(0);
        }
        if (this.currentBarTime > this.currentDayEnd) {
            this.currentDayEnd = SQTime.correctDayEnd((long)this.currentBarTime);
        }
        this.nextBarIndex = n - 1;
        this.Time.setShift(this.nextBarIndex);
        this.nextBarTime = this.Time.get(0);
        this.Time.setShift(n);
        this.Open.setShift(n);
        this.High.setShift(n);
        this.Low.setShift(n);
        this.Close.setShift(n);
        this.Volume.setShift(n);
        this.TimeCurrent = this.Time.get(0);
        this.barLow = Double.MAX_VALUE;
        this.barHigh = -1.7976931348623157E308;
    }

    private void processDailyData(TickEvent tickEvent) throws TradingException {
        long l = tickEvent.getTime();
        double d = tickEvent.getBid();
        this.ensureDWMExists(1);
        if (this.useSessionWhenComputingDWM && this.sessionDaily == null) {
            this.sessionDaily = SessionManager.getSession((String)this.chartDef.getSession()).clone();
        }
        if (this.TimeD.size() == 0 || l >= this.nextDayTick) {
            if (this.useSessionWhenComputingDWM) {
                this.sessionDaily.clearSessionTempData();
                this.sessionDaily.fixD1DataTime(tickEvent);
                this.sessionDaily.checkTimeIsInSession(tickEvent.getTime(), this.sessionStatus, "D1");
            }
            if (!this.useSessionWhenComputingDWM || this.sessionStatus.sessionStartTime == Long.MIN_VALUE) {
                this.sessionStatus.sessionStartTime = l;
                this.sessionStatus.sessionStartTime = SQTime.setHour((long)this.sessionStatus.sessionStartTime, (int)0);
                this.sessionStatus.sessionStartTime = SQTime.setMinute((long)this.sessionStatus.sessionStartTime, (int)0);
                this.sessionStatus.sessionStartTime = SQTime.setSecond((long)this.sessionStatus.sessionStartTime, (int)0);
                this.sessionStatus.sessionStartTime = SQTime.setMiliSeconds((long)this.sessionStatus.sessionStartTime, (int)0);
                this.sessionStatus.sessionEndTime = SQTime.correctDayEnd((long)this.sessionStatus.sessionStartTime);
            }
            boolean bl = this.barType.getBarTimeType() == 2;
            this.TimeD.add(bl ? this.sessionStatus.sessionEndTime : this.sessionStatus.sessionStartTime);
            this.OpenD.add(d);
            this.HighD.add(d);
            this.LowD.add(d);
            this.CloseD.add(d);
            this.dailyHigh = d;
            this.dailyLow = d;
            this.nextDayTick = SQTime.addDays((long)this.sessionStatus.sessionStartTime, (int)1);
        } else {
            if (d > this.dailyHigh) {
                this.HighD.set(0, d);
                this.dailyHigh = d;
            }
            if (d < this.dailyLow) {
                this.LowD.set(0, d);
                this.dailyLow = d;
            }
            this.CloseD.set(0, d);
        }
    }

    private void ensureDWMExists(int n) {
        switch (n) {
            case 1: {
                if (this.TimeD != null) break;
                this.TimeD = new TimeDataSeries("TimeD", 1000, this.chartDef);
                this.OpenD = new DataSeries("OpenD", 1000, this.chartDef);
                this.HighD = new DataSeries("HighD", 1000, this.chartDef);
                this.LowD = new DataSeries("LowD", 1000, this.chartDef);
                this.CloseD = new DataSeries("CloseD", 1000, this.chartDef);
                break;
            }
            case 2: {
                if (this.TimeW != null) break;
                this.TimeW = new TimeDataSeries("TimeW", 200, this.chartDef);
                this.OpenW = new DataSeries("OpenW", 200, this.chartDef);
                this.HighW = new DataSeries("HighW", 200, this.chartDef);
                this.LowW = new DataSeries("LowW", 200, this.chartDef);
                this.CloseW = new DataSeries("CloseW", 200, this.chartDef);
                break;
            }
            case 3: {
                if (this.TimeM != null) break;
                this.TimeM = new TimeDataSeries("TimeM", 50, this.chartDef);
                this.OpenM = new DataSeries("OpenM", 50, this.chartDef);
                this.HighM = new DataSeries("HighM", 50, this.chartDef);
                this.LowM = new DataSeries("LowM", 50, this.chartDef);
                this.CloseM = new DataSeries("CloseM", 50, this.chartDef);
            }
        }
    }

    private void processWeeklyData(TickEvent tickEvent) throws TradingException {
        long l = tickEvent.getTime();
        double d = tickEvent.getBid();
        this.ensureDWMExists(2);
        if (this.useSessionWhenComputingDWM && this.sessionWeekly == null) {
            this.sessionWeekly = SessionManager.getSession((String)this.chartDef.getSession()).clone();
        }
        if (this.TimeW.size() == 0 || l >= this.nextWeekTick) {
            if (this.useSessionWhenComputingDWM) {
                this.sessionWeekly.clearSessionTempData();
                this.sessionWeekly.fixD1DataTime(tickEvent);
                this.sessionWeekly.checkTimeIsInSession(tickEvent.getTime(), this.sessionStatus, "Weekly");
            }
            if (!this.useSessionWhenComputingDWM || this.sessionStatus.sessionStartTime == Long.MIN_VALUE) {
                this.sessionStatus.sessionStartTime = l;
                this.sessionStatus.sessionStartTime = SQTime.setHour((long)this.sessionStatus.sessionStartTime, (int)0);
                this.sessionStatus.sessionStartTime = SQTime.setMinute((long)this.sessionStatus.sessionStartTime, (int)0);
                this.sessionStatus.sessionStartTime = SQTime.setSecond((long)this.sessionStatus.sessionStartTime, (int)0);
                this.sessionStatus.sessionStartTime = SQTime.setMiliSeconds((long)this.sessionStatus.sessionStartTime, (int)0);
                this.sessionStatus.sessionStartTime = SQTime.setDayOfWeek((long)this.sessionStatus.sessionStartTime, (int)1);
                this.sessionStatus.sessionEndTime = SQTime.setDayOfWeek((long)this.sessionStatus.sessionStartTime, (int)7);
                this.sessionStatus.sessionEndTime = SQTime.correctDayEnd((long)this.sessionStatus.sessionEndTime);
            }
            boolean bl = this.barType.getBarTimeType() == 2;
            this.TimeW.add(bl ? this.sessionStatus.sessionEndTime : this.sessionStatus.sessionStartTime);
            this.OpenW.add(d);
            this.HighW.add(d);
            this.LowW.add(d);
            this.CloseW.add(d);
            this.weeklyHigh = d;
            this.weeklyLow = d;
            this.nextWeekTick = SQTime.addDays((long)this.sessionStatus.sessionStartTime, (int)7);
        } else {
            if (d > this.weeklyHigh) {
                this.HighW.set(0, d);
                this.weeklyHigh = d;
            }
            if (d < this.weeklyLow) {
                this.LowW.set(0, d);
                this.weeklyLow = d;
            }
            this.CloseW.set(0, d);
        }
    }

    private void processMonthlyData(TickEvent tickEvent) throws TradingException {
        long l = tickEvent.getTime();
        double d = tickEvent.getBid();
        this.ensureDWMExists(3);
        if (this.useSessionWhenComputingDWM && this.sessionMonthly == null) {
            this.sessionMonthly = SessionManager.getSession((String)this.chartDef.getSession()).clone();
        }
        if (this.TimeM.size() == 0 || l >= this.nextMonthTick) {
            if (this.useSessionWhenComputingDWM) {
                this.sessionMonthly.clearSessionTempData();
                this.sessionMonthly.fixD1DataTime(tickEvent);
                this.sessionMonthly.checkTimeIsInSession(tickEvent.getTime(), this.sessionStatus, "Monthly");
            }
            if (!this.useSessionWhenComputingDWM || this.sessionStatus.sessionStartTime == Long.MIN_VALUE) {
                this.sessionStatus.sessionStartTime = l;
                this.sessionStatus.sessionStartTime = SQTime.setHour((long)this.sessionStatus.sessionStartTime, (int)0);
                this.sessionStatus.sessionStartTime = SQTime.setMinute((long)this.sessionStatus.sessionStartTime, (int)0);
                this.sessionStatus.sessionStartTime = SQTime.setSecond((long)this.sessionStatus.sessionStartTime, (int)0);
                this.sessionStatus.sessionStartTime = SQTime.setMiliSeconds((long)this.sessionStatus.sessionStartTime, (int)0);
                this.sessionStatus.sessionStartTime = SQTime.setDayOfMonth((long)this.sessionStatus.sessionStartTime, (int)1);
                this.sessionStatus.sessionEndTime = SQTime.addMonths((long)this.sessionStatus.sessionStartTime, (int)1) - 1L;
            }
            boolean bl = this.barType.getBarTimeType() == 2;
            this.TimeM.add(bl ? this.sessionStatus.sessionEndTime : this.sessionStatus.sessionStartTime);
            this.OpenM.add(d);
            this.HighM.add(d);
            this.LowM.add(d);
            this.CloseM.add(d);
            this.monthlyHigh = d;
            this.monthlyLow = d;
            this.nextMonthTick = SQTime.addMonths((long)this.sessionStatus.sessionStartTime, (int)1);
            this.nextMonthTick = SQTime.setDayOfMonth((long)this.nextMonthTick, (int)1);
        } else {
            if (d > this.monthlyHigh) {
                this.HighM.set(0, d);
                this.monthlyHigh = d;
            }
            if (d < this.monthlyLow) {
                this.LowM.set(0, d);
                this.monthlyLow = d;
            }
            this.CloseM.set(0, d);
        }
    }

    private void createBarData(TickEvent tickEvent, long l) throws Exception {
        double d = tickEvent.getBid();
        this.updateVariables(tickEvent.getTime(), d, tickEvent.getAsk());
        this.Time.add(l);
        this.Open.add(d);
        this.High.add(d);
        this.Low.add(d);
        this.Close.add(d);
        this.Volume.add(tickEvent.getVolume());
        this.barHigh = d;
        this.barLow = d;
        this.barVolume = tickEvent.getVolume();
        this.EventType = 2;
    }

    private void updateBarData(TickEvent tickEvent, boolean bl) throws Exception {
        double d = tickEvent.getBid();
        this.updateVariables(tickEvent.getTime(), d, tickEvent.getAsk());
        if (d > this.barHigh) {
            this.High.set(0, d, bl);
            this.barHigh = d;
        }
        if (d < this.barLow) {
            this.Low.set(0, d, bl);
            this.barLow = d;
        }
        this.Close.set(0, d, bl);
        if (tickEvent.getVolume() != 0.0) {
            this.barVolume += tickEvent.getVolume();
            this.Volume.set(0, this.barVolume, bl);
        }
        this.EventType = 4;
    }

    private void callDataChangeListeners() throws TradingException {
        this.Time.callDataChangeListeners();
        this.Open.callDataChangeListeners();
        this.High.callDataChangeListeners();
        this.Low.callDataChangeListeners();
        this.Close.callDataChangeListeners();
        this.Volume.callDataChangeListeners();
    }

    private void updateVariables(long l, double d, double d2) {
        this.TimeCurrent = l;
        this.Bid = d;
        this.Ask = d2;
        if (this.connectedObject != null) {
            this.connectedObject.TimeCurrent = this.TimeCurrent;
            this.connectedObject.Bid = this.Bid;
            this.connectedObject.Ask = this.Ask;
        }
    }

    public void processTickSimplified(TickEvent tickEvent, int n) throws Exception {
        if (this.connectionHash != tickEvent.getConnectionHash()) {
            return;
        }
        if (this.symbolHash != tickEvent.getSymbolHash()) {
            return;
        }
        this.barType.processTick(tickEvent, this.barTypeStatus, n);
        if (this.barTypeStatus.status == 0) {
            return;
        }
        if (this.barTypeStatus.status == 2) {
            this.updateBarData(tickEvent, true);
        } else {
            this.createBarData(tickEvent, this.barTypeStatus.barTime);
        }
    }

    public DataSeries getSeries(int n) throws TradingException {
        return this.getSeries(n, this.chartTF);
    }

    public DataSeries getSeries(int n, int n2) throws TradingException {
        if (n2 == 0 || n == 4 || n == 5 || n == 6) {
            switch (n) {
                case 1: {
                    return this.Open;
                }
                case 2: {
                    return this.High;
                }
                case 3: {
                    return this.Low;
                }
                case 0: {
                    return this.Close;
                }
                case 4: {
                    return this.Median;
                }
                case 5: {
                    return this.Typical;
                }
                case 6: {
                    return this.Weighted;
                }
                case 7: {
                    return this.Volume;
                }
            }
        } else if (n2 == 1) {
            this.ensureDWMExists(1);
            switch (n) {
                case 1: {
                    return this.OpenD;
                }
                case 2: {
                    return this.HighD;
                }
                case 3: {
                    return this.LowD;
                }
                case 0: {
                    return this.CloseD;
                }
            }
        } else if (n2 == 2) {
            this.ensureDWMExists(2);
            switch (n) {
                case 1: {
                    return this.OpenW;
                }
                case 2: {
                    return this.HighW;
                }
                case 3: {
                    return this.LowW;
                }
                case 0: {
                    return this.CloseW;
                }
            }
        } else if (n2 == 3) {
            this.ensureDWMExists(3);
            switch (n) {
                case 1: {
                    return this.OpenM;
                }
                case 2: {
                    return this.HighM;
                }
                case 3: {
                    return this.LowM;
                }
                case 0: {
                    return this.CloseM;
                }
            }
        }
        throw new TradingException("Unknown DataSerie type: " + n + ", ChartTF: " + n2);
    }

    public void destroy() {
        if (this.Time != null) {
            this.Time.destroy();
            this.Time = null;
        }
        if (this.Open != null) {
            this.Open.destroy();
            this.Open = null;
        }
        if (this.High != null) {
            this.High.destroy();
            this.High = null;
        }
        if (this.Low != null) {
            this.Low.destroy();
            this.Low = null;
        }
        if (this.Close != null) {
            this.Close.destroy();
            this.Close = null;
        }
        if (this.Volume != null) {
            this.Volume.destroy();
            this.Volume = null;
        }
        if (!this.usesSameDailyDataSeries()) {
            if (this.TimeD != null) {
                this.TimeD.destroy();
                this.TimeD = null;
            }
            if (this.OpenD != null) {
                this.OpenD.destroy();
                this.OpenD = null;
            }
            if (this.HighD != null) {
                this.HighD.destroy();
                this.HighD = null;
            }
            if (this.LowD != null) {
                this.LowD.destroy();
                this.LowD = null;
            }
            if (this.CloseD != null) {
                this.CloseD.destroy();
                this.CloseD = null;
            }
            if (this.TimeW != null) {
                this.TimeW.destroy();
                this.TimeW = null;
            }
            if (this.OpenW != null) {
                this.OpenW.destroy();
                this.OpenW = null;
            }
            if (this.HighW != null) {
                this.HighW.destroy();
                this.HighW = null;
            }
            if (this.LowW != null) {
                this.LowW.destroy();
                this.LowW = null;
            }
            if (this.CloseW != null) {
                this.CloseW.destroy();
                this.CloseW = null;
            }
            if (this.TimeM != null) {
                this.TimeM.destroy();
                this.TimeM = null;
            }
            if (this.OpenM != null) {
                this.OpenM.destroy();
                this.OpenM = null;
            }
            if (this.HighM != null) {
                this.HighM.destroy();
                this.HighM = null;
            }
            if (this.LowM != null) {
                this.LowM.destroy();
                this.LowM = null;
            }
            if (this.CloseM != null) {
                this.CloseM.destroy();
                this.CloseM = null;
            }
        }
        if (this.Typical != null) {
            this.Typical.destroy();
            this.Typical = null;
        }
        if (this.Median != null) {
            this.Median.destroy();
            this.Median = null;
        }
        if (this.Weighted != null) {
            this.Weighted.destroy();
            this.Weighted = null;
        }
    }

    public InstrumentInfo getInstrumentInfo() {
        return this.SymbolInfo;
    }

    public void setInstrumentInfo(InstrumentInfo instrumentInfo) {
        this.SymbolInfo = instrumentInfo;
    }

    public double MinMove() {
        if (this.SymbolInfo == null) {
            return 25.0;
        }
        return this.SymbolInfo.tickStep * this.PriceScale();
    }

    public double BigPointValue() {
        if (this.SymbolInfo == null) {
            return 20.0;
        }
        return this.SymbolInfo.pointValue;
    }

    public double PriceScale() {
        if (this.SymbolInfo == null) {
            return 100.0;
        }
        return Math.pow(10.0, this.SymbolInfo.decimals);
    }

    public double getMinDistance() {
        return this.chartDef != null ? this.chartDef.getMinDistance() : this.MarketData.Chart(0).getMinDistance();
    }

    public void resetPreparedDataShifts() {
        int n = this.Time.size() - 1;
        this.Time.setShift(n);
        this.Open.setShift(n);
        this.High.setShift(n);
        this.Low.setShift(n);
        this.Close.setShift(n);
        this.currentBarTime = Long.MIN_VALUE;
        this.currentDayEnd = Long.MIN_VALUE;
        this.nextBarTime = Long.MIN_VALUE;
    }

    public void setPerformanceParams(boolean bl, boolean bl2, boolean bl3, boolean bl4) {
        this.hasOnTickRule = bl;
        this.hasDailyDataBlock = bl2;
        this.hasWeeklyDataBlock = bl3;
        this.hasMonthlyDataBlock = bl4;
    }

    public int getCurrentBar() {
        return this.currentBar;
    }

    public void setCurrentBar(int n, int n2) {
        this.currentBar = this.Bars() - n - n2;
    }

    public int getSerieIndex() {
        return this.serieIndex;
    }

    public ChartData cloneForTF(int n) {
        if (n != 1 && n != 2 && n != 3) {
            return this;
        }
        ChartData chartData = new ChartData();
        chartData.Time = this.Time;
        chartData.Open = this.Open;
        chartData.High = this.High;
        chartData.Low = this.Low;
        chartData.Close = this.Close;
        chartData.Median = this.Median;
        chartData.Typical = this.Typical;
        chartData.Weighted = this.Weighted;
        chartData.TimeD = this.TimeD;
        chartData.OpenD = this.OpenD;
        chartData.HighD = this.HighD;
        chartData.LowD = this.LowD;
        chartData.CloseD = this.CloseD;
        chartData.TimeW = this.TimeW;
        chartData.OpenW = this.OpenW;
        chartData.HighW = this.HighW;
        chartData.LowW = this.LowW;
        chartData.CloseW = this.CloseW;
        chartData.TimeM = this.TimeM;
        chartData.OpenM = this.OpenM;
        chartData.HighM = this.HighM;
        chartData.LowM = this.LowM;
        chartData.CloseM = this.CloseM;
        chartData.Volume = this.Volume;
        chartData.MarketData = this.MarketData;
        chartData.Connection = this.Connection;
        chartData.Symbol = this.Symbol;
        chartData.Instrument = this.Instrument;
        chartData.Timeframe = this.Timeframe;
        chartData.session = this.session;
        chartData.requestedEventType = this.requestedEventType;
        chartData.connectionHash = this.connectionHash;
        chartData.symbolHash = this.symbolHash;
        chartData.updated = this.updated;
        chartData.barType = this.barType;
        chartData.SymbolInfo = this.SymbolInfo;
        chartData.TimeCurrent = this.TimeCurrent;
        chartData.chartDef = this.chartDef;
        chartData.chartTF = n;
        chartData.Time = this.Time;
        return chartData;
    }

    public ChartData cloneOnlyTF(int n) {
        if (n != 1 && n != 2 && n != 3) {
            return this;
        }
        ChartData chartData = new ChartData();
        if (n == 1) {
            this.ensureDWMExists(1);
            chartData.Time = this.TimeD;
            chartData.Open = this.OpenD;
            chartData.High = this.HighD;
            chartData.Low = this.LowD;
            chartData.Close = this.CloseD;
        } else if (n == 2) {
            this.ensureDWMExists(2);
            chartData.Time = this.TimeW;
            chartData.Open = this.OpenW;
            chartData.High = this.HighW;
            chartData.Low = this.LowW;
            chartData.Close = this.CloseW;
        } else if (n == 3) {
            this.ensureDWMExists(3);
            chartData.Time = this.TimeM;
            chartData.Open = this.OpenM;
            chartData.High = this.HighM;
            chartData.Low = this.LowM;
            chartData.Close = this.CloseM;
        }
        chartData.Volume = this.Volume;
        chartData.MarketData = this.MarketData;
        chartData.Connection = this.Connection;
        chartData.Symbol = this.Symbol;
        chartData.Instrument = this.Instrument;
        chartData.Timeframe = this.Timeframe;
        chartData.session = this.session;
        chartData.requestedEventType = this.requestedEventType;
        chartData.connectionHash = this.connectionHash;
        chartData.symbolHash = this.symbolHash;
        chartData.updated = this.updated;
        chartData.barType = this.barType;
        chartData.SymbolInfo = this.SymbolInfo;
        chartData.TimeCurrent = this.TimeCurrent;
        chartData.chartDef = this.chartDef;
        chartData.chartTF = n;
        chartData.Time = this.Time;
        return chartData;
    }

    public boolean isNewBarOnMainSymbolTF(TickEvent tickEvent) {
        if (this.connectionHash != tickEvent.getConnectionHash()) {
            return false;
        }
        if (this.symbolHash != tickEvent.getSymbolHash()) {
            return false;
        }
        return this.currentBarTime == Long.MIN_VALUE || this.nextBarTime > Long.MIN_VALUE && tickEvent.getTime() >= this.nextBarTime && this.nextBarTime > this.currentBarTime;
    }

    public int getIndyStartingBar() {
        return this.indyStartingBar;
    }

    public void setIndyStartingBar(int n) {
        this.indyStartingBar = n;
    }
}

