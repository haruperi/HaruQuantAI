/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.data;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.SymbolData;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.data.BatchProgressController;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.InstrumentValueEvaluator;
import com.strategyquant.datalib.historyData.dto.TickerDto;
import com.strategyquant.datalib.historyData.dto.TickerKind;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import java.io.File;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.locks.ReentrantLock;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DukasDataManager {
    public static final Logger Log = LoggerFactory.getLogger(DukasDataManager.class);
    public static Set<String> FREE_M1_SYMBOLS = Set.of("EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "EURJPY", "GBPJPY", "CADJPY", "INDEXY", "US500", "USATECH", "USA30", "WTI", "BRENT", "XAUUSD");
    private static final String dataListPath = SQPaths.pluginsDirPath + "/DataSourceDukascopy/dukascopy.csv";
    private static final String dataListLineDelimiter = "\n";
    private static final String dataListValueDelimiter = ";";
    private static final String dataListDateFormat = "dd.MM.yyyy";
    private ArrayList<SymbolData> availableData = new ArrayList();
    private Map<String, SymbolData> availableDataMap = new HashMap<String, SymbolData>();
    private static ReentrantLock lock = new ReentrantLock();
    private static DukasDataManager instance;

    public static synchronized DukasDataManager get() {
        if (instance == null) {
            try {
                lock.lock();
                if (instance == null) {
                    instance = new DukasDataManager();
                }
            }
            finally {
                lock.unlock();
            }
        }
        return instance;
    }

    private DukasDataManager() {
        this.loadSettings();
        this.loadAvailableData();
    }

    public boolean canFreeDownloadFromCdn(DataInfo dataInfo) {
        return FREE_M1_SYMBOLS.contains(dataInfo.uSymbolName) && dataInfo.timeframe.equals("M1");
    }

    private void loadSettings() {
        boolean bl = false;
        if (bl) {
            MainApp.settings().save();
        }
    }

    private void loadAvailableData() {
        try {
            this.availableData.clear();
            this.availableDataMap.clear();
            File file = new File(dataListPath);
            String[] stringArray = SQUtils.fileToString((File)file).split(dataListLineDelimiter);
            int n = 0;
            for (String string : stringArray) {
                String[] stringArray2 = string.split(dataListValueDelimiter);
                ++n;
                if (stringArray2.length != 12) continue;
                try {
                    SymbolData symbolData = new SymbolData();
                    symbolData.symbol = stringArray2[0].trim();
                    symbolData.name = stringArray2[1].trim();
                    symbolData.category = stringArray2[2].trim();
                    symbolData.subcategory = stringArray2[3].trim();
                    symbolData.dateFrom = SQTime.parseToMilis((String)stringArray2[4].trim(), (String)dataListDateFormat);
                    symbolData.dateFromM1 = SQTime.parseToMilis((String)stringArray2[5].trim(), (String)dataListDateFormat);
                    symbolData.decimals = Integer.parseInt(stringArray2[6].trim());
                    symbolData.tickValue = Double.parseDouble(stringArray2[7].trim());
                    symbolData.defaultSpread = Double.parseDouble(stringArray2[8].trim());
                    symbolData.tickSize = Double.parseDouble(stringArray2[9].trim());
                    symbolData.tickStep = Double.parseDouble(stringArray2[10].trim());
                    symbolData.instrumentType = Byte.parseByte(stringArray2[11].trim());
                    this.availableData.add(symbolData);
                    this.availableDataMap.put(symbolData.symbol, symbolData);
                }
                catch (Exception exception) {
                    Log.error("Cannot read dukascopy data file line " + n + ". " + exception.getMessage());
                }
            }
        }
        catch (Exception exception) {
            Log.error("Cannot read dukascopy data list file. ", (Throwable)exception);
        }
    }

    public ArrayList<SymbolData> getAvailableDataList() {
        lock.lock();
        try {
            ArrayList<SymbolData> arrayList = DukasDataManager.get().availableData;
            return arrayList;
        }
        finally {
            lock.unlock();
        }
    }

    public SymbolData getAvailableDataInfo(String string) {
        lock.lock();
        try {
            SymbolData symbolData = this.availableDataMap.get(string);
            return symbolData;
        }
        finally {
            lock.unlock();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public String addData(TickerDto tickerDto, String string, String string2, TickerKind tickerKind, String string3, byte by, double d, double d2, double d3, int n) throws Exception {
        String string4 = tickerDto.getTicker();
        String string5 = string4 + string;
        lock.lock();
        try {
            while (DataManager.checkDataExists("History", string5)) {
                string5 = DataManager.generateName(string5);
            }
            double d4 = 0.0;
            double d5 = 0.0;
            String string6 = "History data instrument";
            if (!InstrumentManager.checkInstrumentExists(string3)) {
                InstrumentManager.addInstrument(string3, string6, d3, d2, d, d4, d5, "<Method type=\"None\" use=\"true\"><Params/></Method>", by, null, null, null, null, 1.0, 0.0);
            } else {
                InstrumentInfo instrumentInfo = InstrumentManager.getInstrumentInfo(string3);
                if (instrumentInfo.dataType != by) {
                    InstrumentManager.updateDataType(string3, by);
                }
                if (instrumentInfo.tickSize != d2 || instrumentInfo.tickStep != d) {
                    while (InstrumentManager.checkInstrumentExists(string3)) {
                        string3 = DataManager.generateName(string3);
                    }
                    InstrumentManager.addInstrument(string3, string6, d3, d2, d, d4, d5, "<Method type=\"None\" use=\"true\"><Params/></Method>", by, tickerDto.getMarketName(), null, null, null, 1.0, 0.0);
                }
            }
            int n2 = tickerKind == TickerKind.FUTURES ? 6 : 5;
            String string7 = tickerDto.getName() != null ? tickerDto.getName() : tickerDto.getTicker();
            DataManager.addData("History", string5, string3, n, n2, string4, string7);
            DataManager.updateTimeframe("History", string5, string2);
        }
        finally {
            lock.unlock();
        }
        return string5;
    }

    private double getTickerValue(BigDecimal bigDecimal) {
        if (bigDecimal == null) {
            throw new RuntimeException(L.t((String)"Symbol is not set properly - some necessary attributes are missing (tick step,tick size, point value, default spread)", (Object[])new Object[0]));
        }
        return bigDecimal.doubleValue();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public String addData(String string, String string2, int n, String string3) throws Exception {
        BrokerDto brokerDto = BrokerManager.getInstance().getBroker(n);
        if (brokerDto == null) {
            throw new RuntimeException("Specified broker was not found");
        }
        String string4 = string + string2;
        String string5 = string3 == null ? string : string3;
        lock.lock();
        try {
            SymbolData symbolData = this.getAvailableDataInfo(string);
            if (symbolData == null) {
                throw new Exception("No info found for symbol '" + string + "'.");
            }
            while (DataManager.checkDataExists("History", string4)) {
                string4 = DataManager.generateName(string4);
            }
            if (!InstrumentManager.checkInstrumentExists(string5)) {
                if (string3 != null) {
                    throw new RuntimeException(L.t((String)"Instrument %s for broker %s doesn't exists. Symbol can't be added.", (Object[])new Object[]{string5, brokerDto.getName()}));
                }
                InstrumentManager.addInstrument(string5, "Dukascopy instrument", symbolData.tickValue, symbolData.tickSize, symbolData.tickStep, symbolData.defaultSpread, symbolData.defaultSlippage, "<Method type=\"None\" use=\"true\"><Params/></Method>", symbolData.instrumentType, null, null, null, null, 1.0, 0.0);
            } else if (n == -1) {
                InstrumentInfo instrumentInfo = InstrumentManager.getInstrumentInfo(string5);
                if (instrumentInfo.tickSize != symbolData.tickSize || instrumentInfo.tickStep != symbolData.tickStep) {
                    while (InstrumentManager.checkInstrumentExists(string5)) {
                        string5 = DataManager.generateName(string5);
                    }
                    InstrumentManager.addInstrument(string5, n, "Dukascopy instrument", symbolData.tickValue, symbolData.tickSize, symbolData.tickStep, symbolData.defaultSpread, symbolData.defaultSlippage, 0.0, "<Method type=\"None\" use=\"true\"><Params/></Method>", symbolData.instrumentType, null, null, null, null, 1.0, 0.0);
                }
            }
            DataManager.addData("History", string4, string5, 1, 2, string, symbolData.name, -1, n);
        }
        finally {
            lock.unlock();
        }
        return string4;
    }

    public void addBatch(List<DataInfo> list, Map<String, TickerDto> map, InstrumentValueEvaluator instrumentValueEvaluator, BatchProgressController batchProgressController) throws Exception {
        Map<String, InstrumentInfo> map2 = InstrumentManager.list().stream().collect(Collectors.toMap(instrumentInfo -> instrumentInfo.instrument, instrumentInfo -> instrumentInfo));
        Set set = DataManager.list().stream().map(dataInfo -> dataInfo.symbol).collect(Collectors.toSet());
        LinkedList<InstrumentInfo> linkedList = new LinkedList<InstrumentInfo>();
        for (DataInfo dataInfo2 : list) {
            InstrumentInfo instrumentInfo2;
            InstrumentInfo instrumentInfo3;
            TickerDto tickerDto = map.get(dataInfo2.uSymbol);
            String string = dataInfo2.symbol;
            Log.debug("Adding symbol: {}", (Object)string);
            while (set.contains(string)) {
                string = DataManager.generateName(string);
                Log.debug("Generated new symbol: {}", (Object)string);
            }
            dataInfo2.symbol = string;
            set.add(string);
            String string2 = tickerDto.getName() != null ? tickerDto.getName() : tickerDto.getTicker();
            dataInfo2.uSymbol = tickerDto.getTicker();
            dataInfo2.uSymbolName = string2;
            dataInfo2.timeframe = tickerDto.isEod() ? "D1" : "M1";
            byte by = instrumentValueEvaluator.getInstrumentType(tickerDto);
            double d = instrumentValueEvaluator.getTickSize(tickerDto);
            double d2 = instrumentValueEvaluator.getTickStep(tickerDto);
            double d3 = instrumentValueEvaluator.getPointValue(tickerDto);
            double d4 = instrumentValueEvaluator.getOrderSizeMultiplier(tickerDto);
            double d5 = instrumentValueEvaluator.getOrderSizeStep(tickerDto);
            if (!map2.containsKey(dataInfo2.instrument)) {
                instrumentInfo3 = new InstrumentInfo();
                instrumentInfo3.description = instrumentValueEvaluator.getDescriptions(tickerDto);
                instrumentInfo3.instrument = dataInfo2.instrument;
                instrumentInfo3.tickStep = d2;
                instrumentInfo3.tickSize = d;
                instrumentInfo3.pointValue = d3;
                instrumentInfo3.orderSizeMultiplier = d4;
                instrumentInfo3.orderSizeStep = d5;
                instrumentInfo3.commissions = "<Method type=\"None\" use=\"true\"><Params/></Method>";
                instrumentInfo3.exchange = tickerDto.getMarketName();
                instrumentInfo3.dataType = by;
                linkedList.add(instrumentInfo3);
                map2.put(instrumentInfo3.instrument, instrumentInfo3);
                continue;
            }
            instrumentInfo3 = map2.get(dataInfo2.instrument);
            if (this.matchInstrument(instrumentInfo3, d, d2, d4, d5, by)) continue;
            String string3 = dataInfo2.instrument;
            boolean bl = false;
            while (map2.containsKey(string3)) {
                instrumentInfo2 = map2.get(string3 = DataManager.generateName(string3));
                if (instrumentInfo2 == null || !this.matchInstrument(instrumentInfo2, d, d2, d4, d5, by)) continue;
                bl = true;
                dataInfo2.instrument = string3;
                break;
            }
            if (bl) continue;
            instrumentInfo2 = new InstrumentInfo();
            instrumentInfo2.description = instrumentValueEvaluator.getDescriptions(tickerDto);
            instrumentInfo2.instrument = string3;
            instrumentInfo2.tickStep = d2;
            instrumentInfo2.tickSize = d;
            instrumentInfo2.pointValue = d3;
            instrumentInfo2.exchange = tickerDto.getMarketName();
            instrumentInfo2.commissions = "<Method type=\"None\" use=\"true\"><Params/></Method>";
            instrumentInfo2.dataType = by;
            instrumentInfo2.orderSizeMultiplier = d4;
            instrumentInfo2.orderSizeStep = d5;
            linkedList.add(instrumentInfo2);
            map2.put(instrumentInfo2.instrument, instrumentInfo2);
            dataInfo2.instrument = string3;
        }
        if (!linkedList.isEmpty()) {
            InstrumentManager.addInstrumentInBatch(linkedList);
        }
        for (DataInfo dataInfo2 : list) {
            dataInfo2.symbolInfo = InstrumentManager.getInstrumentInfo(dataInfo2.instrument);
        }
        DataManager.addDataInBatch("History", list, batchProgressController);
    }

    private boolean matchInstrument(InstrumentInfo instrumentInfo, double d, double d2, double d3, double d4, int n) {
        return instrumentInfo.tickSize == d && instrumentInfo.tickStep == d2 && instrumentInfo.dataType == n && instrumentInfo.orderSizeMultiplier == d3 && instrumentInfo.orderSizeStep == d4;
    }
}

