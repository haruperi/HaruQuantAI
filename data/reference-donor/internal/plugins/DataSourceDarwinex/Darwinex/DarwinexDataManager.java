/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.SymbolData
 *  com.strategyquant.datalib.broker.BrokerDto
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.Darwinex;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.SymbolData;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.locks.ReentrantLock;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DarwinexDataManager {
    public static final Logger Log = LoggerFactory.getLogger(DarwinexDataManager.class);
    public static final String DOWNLOAD_DARWINEX_SYMBOL_JOB = "DownloadDarwinexSymbolJob_";
    private static final String dataListPath = SQPaths.pluginsDirPath + "/DataSourceDarwinex/darwinex.csv";
    private static final String dataListLineDelimiter = "\n";
    private static final String dataListValueDelimiter = ";";
    private static final String dataListDateFormat = "dd.MM.yyyy";
    private ArrayList<SymbolData> availableData = new ArrayList();
    private Map<String, SymbolData> availableDataMap = new HashMap<String, SymbolData>();
    private static ReentrantLock lock = new ReentrantLock();
    private static DarwinexDataManager instance;

    public static synchronized DarwinexDataManager get() {
        if (instance == null) {
            try {
                lock.lock();
                if (instance == null) {
                    instance = new DarwinexDataManager();
                }
            }
            finally {
                lock.unlock();
            }
        }
        return instance;
    }

    private DarwinexDataManager() {
        this.loadSettings();
        this.loadAvailableData();
    }

    private void loadSettings() {
        boolean save = false;
        if (save) {
            MainApp.settings().save();
        }
    }

    private void loadAvailableData() {
        try {
            this.availableData.clear();
            this.availableDataMap.clear();
            File file = new File(dataListPath);
            String[] lines = SQUtils.fileToString((File)file).split(dataListLineDelimiter);
            int lineNo = 0;
            for (String line : lines) {
                String[] split = line.split(dataListValueDelimiter);
                ++lineNo;
                if (split.length != 8) continue;
                try {
                    SymbolData darwinexData = new SymbolData();
                    darwinexData.name = darwinexData.symbol = split[0].trim();
                    darwinexData.dateFrom = SQTime.parseToMilis((String)split[1].trim(), (String)dataListDateFormat);
                    darwinexData.decimals = Integer.parseInt(split[2].trim());
                    darwinexData.tickValue = Double.parseDouble(split[3].trim());
                    darwinexData.defaultSpread = Double.parseDouble(split[4].trim());
                    darwinexData.tickSize = Double.parseDouble(split[5].trim());
                    darwinexData.tickStep = Double.parseDouble(split[6].trim());
                    darwinexData.instrumentType = Byte.parseByte(split[7].trim());
                    this.availableData.add(darwinexData);
                    this.availableDataMap.put(darwinexData.symbol, darwinexData);
                }
                catch (Exception e) {
                    Log.error("Cannot read Darwinex data file line " + lineNo + ". " + e.getMessage());
                }
            }
        }
        catch (Exception e) {
            Log.error("Cannot read Darwinex data list file. ", (Throwable)e);
        }
    }

    public ArrayList<SymbolData> getAvailableDataList() {
        lock.lock();
        try {
            ArrayList<SymbolData> arrayList = DarwinexDataManager.get().availableData;
            return arrayList;
        }
        finally {
            lock.unlock();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public String suggestSymbols(String symbol) {
        String key = symbol == null ? "" : symbol.trim().toUpperCase();
        StringBuilder sb = new StringBuilder();
        lock.lock();
        try {
            for (SymbolData data : this.availableData) {
                String name = data.symbol.toUpperCase();
                if (key.length() < 2 || !name.contains(key) && !key.contains(name)) continue;
                if (sb.length() > 0) {
                    sb.append(", ");
                }
                sb.append(data.symbol);
            }
        }
        finally {
            lock.unlock();
        }
        if (sb.length() == 0) {
            return L.t((String)"Use -symbol action=darwinexsymbols for the available names.", (Object[])new Object[0]);
        }
        return L.t((String)"Did you mean: %s?", (Object[])new Object[]{sb.toString()});
    }

    public SymbolData getAvailableDataInfo(String symbol) {
        lock.lock();
        try {
            SymbolData symbolData = this.availableDataMap.get(symbol);
            return symbolData;
        }
        finally {
            lock.unlock();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public String addData(String symbol, String postfix, int broker, String requiredInstrumentIdent) throws Exception {
        BrokerDto brokerDto = BrokerManager.getInstance().getBroker(Integer.valueOf(broker));
        if (brokerDto == null) {
            throw new RuntimeException("Specified broker was not found");
        }
        String symbolName = symbol + postfix;
        String instrumentName = requiredInstrumentIdent == null ? symbol : requiredInstrumentIdent;
        lock.lock();
        try {
            SymbolData symbolData = this.getAvailableDataInfo(symbol);
            if (symbolData == null) {
                throw new Exception(L.t((String)"No info found for symbol %s. Check Darwinex config file %s.", (Object[])new Object[]{symbol, dataListPath}) + " " + this.suggestSymbols(symbol));
            }
            while (DataManager.checkDataExists((String)"History", (String)symbolName)) {
                symbolName = this.generateName(symbolName);
            }
            if (!InstrumentManager.checkInstrumentExists((String)instrumentName)) {
                if (requiredInstrumentIdent != null) {
                    throw new RuntimeException(L.t((String)"Instrument %s for broker %s doesn't exists. Symbol can't be added.", (Object[])new Object[]{instrumentName, brokerDto.getName()}));
                }
                InstrumentManager.addInstrument((String)instrumentName, (String)"Darwinex instrument", (double)symbolData.tickValue, (double)symbolData.tickSize, (double)symbolData.tickStep, (double)symbolData.defaultSpread, (double)symbolData.defaultSlippage, (String)"<Method type=\"None\" use=\"true\"><Params/></Method>", (byte)symbolData.instrumentType, null, null, null, null, (double)1.0, (double)0.0);
            } else if (broker == -1) {
                InstrumentInfo instrument = InstrumentManager.getInstrumentInfo((String)instrumentName);
                if (instrument.tickSize != symbolData.tickSize || instrument.tickStep != symbolData.tickStep) {
                    while (InstrumentManager.checkInstrumentExists((String)instrumentName)) {
                        instrumentName = this.generateName(instrumentName);
                    }
                    InstrumentManager.addInstrument((String)instrumentName, (int)broker, (String)"Darwinex instrument", (double)symbolData.tickValue, (double)symbolData.tickSize, (double)symbolData.tickStep, (double)symbolData.defaultSpread, (double)symbolData.defaultSlippage, (double)0.0, (String)"<Method type=\"None\" use=\"true\"><Params/></Method>", (byte)symbolData.instrumentType, null, null, null, null, (double)1.0, (double)0.0);
                }
            }
            DataManager.addData((String)"History", (String)symbolName, (String)instrumentName, (int)1, (int)4, (String)symbol, (String)symbolData.name, (int)-1, (int)broker);
        }
        finally {
            lock.unlock();
        }
        return symbolName;
    }

    private String generateName(String originalName) {
        int bracketStartPos = originalName.lastIndexOf("(");
        int bracketEndPos = originalName.length() - 1;
        int number = 0;
        try {
            String numberStr = originalName.substring(bracketStartPos + 1, bracketEndPos);
            number = Integer.parseInt(numberStr);
        }
        catch (Exception exception) {
            // empty catch block
        }
        if (number > 0) {
            return originalName.substring(0, bracketStartPos) + "(" + (number + 1) + ")";
        }
        bracketStartPos = bracketStartPos < 0 ? originalName.length() : bracketStartPos;
        return originalName.substring(0, bracketStartPos) + "(2)";
    }
}

