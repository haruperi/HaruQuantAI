/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.broker.BrokerDto
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.data.DataDb
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew
 *  com.strategyquant.datalib.historyData.dto.TickerDto
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.crypting.DecryptException
 *  com.strategyquant.lib.historyData.HistoryDataSubscription
 *  org.apache.http.client.ClientProtocolException
 *  org.jdom2.JDOMException
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.data;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.data.DataDb;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.datalib.historyData.dto.TickerDto;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.crypting.DecryptException;
import com.strategyquant.lib.historyData.HistoryDataSubscription;
import com.strategyquant.tradinglib.historyData.HistoryDataManager;
import com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import java.io.File;
import java.io.IOException;
import java.security.NoSuchAlgorithmException;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import org.apache.http.client.ClientProtocolException;
import org.jdom2.JDOMException;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AppDataImporter {
    public static final Logger Log = LoggerFactory.getLogger(AppDataImporter.class);
    private String path;
    private String license;
    private DataDb oldDatabase;
    private List<DataInfo> tickers;
    private List<InstrumentInfo> instruments;
    private String dataRoot;
    private Map<String, InstrumentInfo> instrumentMap;
    private Map<String, InstrumentInfo> newInstrumentMap = new HashMap<String, InstrumentInfo>();
    private boolean publicData;
    private boolean freeSymbol;
    private int total;
    private JSONObject progress;
    private volatile boolean cancel;
    private long dateTo;
    private long dateFrom;
    private int records;
    private List<BrokerDto> brokers;
    private Map<Integer, BrokerDto> brokerMap = new HashMap<Integer, BrokerDto>();
    private Map<Integer, BrokerDto> newBrokerMap = new HashMap<Integer, BrokerDto>();

    public AppDataImporter(String string, String string2) {
        this.path = string;
        this.license = string2;
        this.dataRoot = string + File.separator + "user" + File.separator + "data";
    }

    public void start() throws Exception {
        this.progress = new JSONObject();
        try {
            this.openDatabase();
            this.updateMessage("Reading list of tickers");
            this.tickers = this.readTickers();
            this.updateMessage("Reading list of instruments");
            this.instruments = this.readInstruments();
            this.instrumentMap = this.instruments.stream().collect(Collectors.toMap(instrumentInfo -> instrumentInfo.instrument, instrumentInfo -> instrumentInfo));
            this.brokers = this.readBrokers();
            this.brokerMap = this.brokers.stream().collect(Collectors.toMap(BrokerDto::getId, brokerDto -> brokerDto));
            this.handle();
            this.newInstrumentMap.clear();
        }
        catch (Exception exception) {
            Log.error("Error while importing data", (Throwable)exception);
            this.progress.put("error", (Object)("Error while importing data: " + exception.getMessage()));
            DataManagerAddProgressSender.getInstance().sendData(this.progress);
        }
        finally {
            this.progress.put("percent", 100);
            DataManagerAddProgressSender.getInstance().sendData(this.progress);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void handle() throws Exception {
        this.total = this.tickers.size();
        int n = 0;
        this.updateMessage("Importing data...");
        for (DataInfo dataInfo : this.tickers) {
            boolean bl = false;
            try {
                if (this.cancel) break;
                boolean bl2 = this.publicData = dataInfo.source != 5 && dataInfo.source != 6;
                if (!this.publicData && MainApp.checkProduct((String)"QDM")) continue;
                if (!this.publicData && (this.license == null || this.license.isBlank())) {
                    this.writeToLog(dataInfo, "skipped - no license was inserted");
                    continue;
                }
                if (!this.checkData(dataInfo)) {
                    this.writeToLog(dataInfo, "skipped - not valid subscriptions");
                    continue;
                }
                DataBinReaderNew dataBinReaderNew = this.getDataReader(dataInfo, false);
                String string = dataInfo.symbol;
                while (DataManager.checkDataExists((String)"History", (String)string)) {
                    string = DataManager.generateName((String)string);
                }
                try {
                    if (dataBinReaderNew.isCrypted() && this.publicData) {
                        this.writeToLog(dataInfo, "skipped - invalid symbol's type");
                        continue;
                    }
                    this.performCopy(string, dataInfo, dataBinReaderNew, n, false);
                    this.saveToDatabase(string, dataInfo);
                }
                finally {
                    dataBinReaderNew.closeFile();
                    dataBinReaderNew = null;
                    continue;
                }
                this.writeToLog(dataInfo, "imported");
                if (dataInfo.source == 5 && "M1".equals(dataInfo.timeframe)) {
                    dataBinReaderNew = this.getDataReader(dataInfo, true);
                    try {
                        this.performCopy(string, dataInfo, dataBinReaderNew, n, true);
                    }
                    finally {
                        dataBinReaderNew.closeFile();
                        dataBinReaderNew = null;
                    }
                }
                bl = true;
            }
            catch (DecryptException decryptException) {
                Log.error("", (Throwable)decryptException);
                this.writeToLog(dataInfo, "failed - inserted license is wrong");
            }
            catch (Exception exception) {
                Log.error("", (Throwable)exception);
                this.writeToLog(dataInfo, "failed - " + exception.getMessage());
            }
            finally {
                this.updateProgress(dataInfo.symbol, ++n, bl);
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void performCopy(String string, DataInfo dataInfo, DataBinReaderNew dataBinReaderNew, int n, boolean bl) throws Exception {
        String string2 = bl ? L.t((String)"Importing unadjusted data (%d/%d) for symbol %s", (Object[])new Object[]{n + 1, this.total, dataInfo.symbol}) : L.t((String)"Importing data (%d/%d) for symbol %s", (Object[])new Object[]{n + 1, this.total, dataInfo.symbol});
        this.updateMessage(string2);
        DataBinWriterNew dataBinWriterNew = this.getDataWriter(string, dataInfo, bl);
        File file = new File(dataBinWriterNew.getFileName());
        if (file.exists()) {
            file.delete();
        }
        try {
            this.copy(dataInfo, dataBinReaderNew, dataBinWriterNew, string2);
        }
        finally {
            dataBinWriterNew.close();
            String string3 = dataBinWriterNew.getFileName().substring(0, dataBinWriterNew.getFileName().length() - 4);
            File file2 = new File(string3);
            if (file2.exists()) {
                file2.delete();
            }
            file.renameTo(file2);
            dataBinWriterNew = null;
        }
    }

    private void writeToLog(DataInfo dataInfo, String string) {
        DataManagerProgressListener dataManagerProgressListener = (DataManagerProgressListener)DataManagerDataProgress.get().createListener(dataInfo.symbol, null);
        dataManagerProgressListener.setMessage(string);
        DataManagerDataProgress.get().removeListener(dataInfo.symbol);
    }

    private void updateProgress(String string, int n, boolean bl) {
        Integer n2 = SQUtils.round((double)(100.0 * (double)n / (double)this.total));
        this.progress.put("percent", (Object)n2);
        if (bl) {
            this.progress.put("info", (Object)L.t((String)"Importing symbol '%s' finished", (Object[])new Object[]{string}));
        } else {
            this.progress.put("info", (Object)L.t((String)"Importing symbol '%s' failed", (Object[])new Object[]{string}));
        }
        DataManagerAddProgressSender.getInstance().sendData(this.progress);
    }

    private void updateMessage(String string) {
        this.progress.put("info", (Object)string);
        DataManagerAddProgressSender.getInstance().sendData(this.progress);
    }

    private boolean checkData(DataInfo dataInfo) throws ClientProtocolException, IllegalStateException, NoSuchAlgorithmException, SQLException, IOException, JDOMException {
        boolean bl;
        if (this.publicData) {
            return true;
        }
        boolean bl2 = dataInfo.timeframe.equals("D1");
        boolean bl3 = bl = dataInfo.source == 5;
        if (bl) {
            this.freeSymbol = HistoryDataSubscription.getInstance().isFreeSymbol(dataInfo.uSymbol, false, bl2);
            return HistoryDataSubscription.getInstance().isAllowedEquity(dataInfo.uSymbol, bl2);
        }
        this.freeSymbol = HistoryDataSubscription.getInstance().isFreeSymbol(dataInfo.uSymbol, true, bl2);
        TickerDto tickerDto = HistoryDataManager.get().getFutureTicker(dataInfo.uSymbol);
        String string = tickerDto == null ? null : tickerDto.getMarketName();
        return HistoryDataSubscription.getInstance().isAllowedFuture(dataInfo.uSymbol, string == null ? "X" : string, bl2);
    }

    private void saveToDatabase(String string, DataInfo dataInfo) throws Exception {
        DataInfo dataInfo2 = new DataInfo();
        dataInfo2.barTimeType = dataInfo.barTimeType;
        dataInfo2.timeframe = dataInfo.timeframe;
        dataInfo2.timezone = dataInfo.timezone;
        dataInfo2.connection = "History";
        dataInfo2.symbol = string;
        dataInfo2.source = dataInfo.source;
        dataInfo2.sourceDataId = dataInfo.sourceDataId;
        dataInfo2.uSymbol = dataInfo.uSymbol;
        dataInfo2.uSymbolName = dataInfo.uSymbolName;
        InstrumentInfo instrumentInfo = this.getOrCreateInstrument(dataInfo.instrument);
        dataInfo2.instrument = instrumentInfo.instrument;
        dataInfo2.brokerId = this.getOrCreateBroker(dataInfo.brokerId).getId();
        DataManager.addData((String)"History", (String)dataInfo2.symbol, (String)instrumentInfo.instrument, (int)dataInfo2.barTimeType, (int)dataInfo2.source, (String)dataInfo2.uSymbol, (String)dataInfo2.uSymbolName, (int)-1, (int)dataInfo2.brokerId);
        int n = SQTime.getDaysBetween((long)this.dateFrom, (long)this.dateTo) + 1;
        long l = n * 86400;
        DataManager.updateData((String)"History", (String)dataInfo2.symbol, (long)this.dateFrom, (long)this.dateTo, (int)this.records, (long)l, (int)dataInfo2.barTimeType, (String)dataInfo2.timeframe, (String)"Etc/UCT");
        try {
            SQWebSocketManager.addToDataQueue(WSDataObjects.getData(string, "download"), "SQUANT", "QDM", "AlgoWizard");
        }
        catch (Exception exception) {
            Log.error("Cannot send data Websocket message. ", (Throwable)exception);
        }
    }

    private DataBinWriterNew getDataWriter(String string, DataInfo dataInfo, boolean bl) throws Exception {
        DataBinWriterNew dataBinWriterNew;
        int n;
        if (this.publicData) {
            n = dataInfo.timeframe.equals("TICK") ? 2 : 1;
            dataBinWriterNew = DataBinWriterNew.getInstance((int)n, (String)MainApp.getDataPath(), null);
        } else {
            n = HistoryDataSubscription.getInstance().isFreeSymbol(dataInfo.uSymbol, dataInfo.sourceDataId == 6, dataInfo.timeframe.equals("D1")) ? 1 : 0;
            dataBinWriterNew = n != 0 ? DataBinWriterNew.getInstance((int)1, (String)MainApp.getDataPath(), (InstrumentInfo)dataInfo.symbolInfo) : DataBinWriterNew.getCryptedInstance((int)1, (String)MainApp.getDataPath(), (InstrumentInfo)dataInfo.symbolInfo);
        }
        String string2 = DataManager.getSymbolFolderName((String)DataManager.get()._getDirectory(), (String)"History", (String)string, (DataInfo)dataInfo);
        String string3 = bl ? "unadjusted" : "";
        File file = new File(string2, DataManager.fixFilename((String)(string + string3 + "_" + dataInfo.timeframe + ".dat.tmp")));
        if (file.exists()) {
            file.delete();
        }
        dataBinWriterNew.setFileName(file.getAbsolutePath());
        dataBinWriterNew.open();
        return dataBinWriterNew;
    }

    private InstrumentInfo getOrCreateInstrument(String string) throws Exception {
        InstrumentInfo instrumentInfo = this.newInstrumentMap.get(string);
        if (instrumentInfo != null) {
            return instrumentInfo;
        }
        InstrumentInfo instrumentInfo2 = this.instrumentMap.get(string);
        int n = instrumentInfo2.broker;
        BrokerDto brokerDto = this.getOrCreateBroker(n);
        instrumentInfo2.broker = brokerDto.getId();
        InstrumentInfo instrumentInfo3 = this.findSuitableInstrument(instrumentInfo2);
        if (instrumentInfo3 == null) {
            instrumentInfo3 = this.createInstrument(instrumentInfo2);
        }
        this.newInstrumentMap.put(string, instrumentInfo3);
        return instrumentInfo3;
    }

    private BrokerDto getOrCreateBroker(int n) throws Exception {
        if (n == -1) {
            return BrokerManager.getInstance().getDefaultBroker();
        }
        BrokerDto brokerDto = this.newBrokerMap.get(n);
        if (brokerDto != null) {
            return brokerDto;
        }
        BrokerDto brokerDto2 = this.brokerMap.get(n);
        BrokerDto brokerDto3 = this.findSuitableBroker(brokerDto2);
        if (brokerDto3 == null) {
            brokerDto3 = this.createBroker(brokerDto2);
        }
        this.newBrokerMap.put(n, brokerDto3);
        return brokerDto3;
    }

    private InstrumentInfo findSuitableInstrument(InstrumentInfo instrumentInfo) throws DataException {
        String string = instrumentInfo.instrument;
        String[] stringArray = string.split("\\(");
        string = stringArray[0];
        while (InstrumentManager.checkInstrumentExists((String)string)) {
            InstrumentInfo instrumentInfo2 = InstrumentManager.getInstrumentInfo((String)string);
            if (this.fit(instrumentInfo2, instrumentInfo)) {
                return instrumentInfo2;
            }
            string = DataManager.generateName((String)string);
        }
        return null;
    }

    private BrokerDto findSuitableBroker(BrokerDto brokerDto) throws DataException {
        String string = brokerDto.getName();
        String[] stringArray = string.split("\\(");
        string = stringArray[0];
        while (BrokerManager.getInstance().checkBrokerExists(string)) {
            BrokerDto brokerDto2 = BrokerManager.getInstance().getBroker(string);
            if (this.fit(brokerDto2, brokerDto)) {
                return brokerDto2;
            }
            string = DataManager.generateName((String)string);
        }
        return null;
    }

    private boolean equalValue(Object object, Object object2) {
        if (object == null) {
            return object2 == null;
        }
        if (object2 == null) {
            return false;
        }
        return object.equals(object2);
    }

    private boolean fit(BrokerDto brokerDto, BrokerDto brokerDto2) {
        return brokerDto.isMtUse() == brokerDto2.isMtUse() && brokerDto.isStockPickerUse() == brokerDto2.isStockPickerUse() && this.equalValue(brokerDto.getMtTimezone(), brokerDto2.getMtTimezone()) && this.equalValue(brokerDto.getPostfix(), brokerDto2.getPostfix());
    }

    private boolean fit(InstrumentInfo instrumentInfo, InstrumentInfo instrumentInfo2) {
        return instrumentInfo.tickSize == instrumentInfo2.tickSize && instrumentInfo.tickStep == instrumentInfo2.tickStep && instrumentInfo.dataType == instrumentInfo2.dataType && instrumentInfo.orderSizeMultiplier == instrumentInfo2.orderSizeMultiplier && instrumentInfo.orderSizeStep == instrumentInfo2.orderSizeStep && instrumentInfo.broker == instrumentInfo2.broker;
    }

    private InstrumentInfo createInstrument(InstrumentInfo instrumentInfo) throws Exception, DataException {
        String string = instrumentInfo.instrument;
        while (InstrumentManager.checkInstrumentExists((String)string)) {
            string = DataManager.generateName((String)string);
        }
        InstrumentManager.addInstrument((String)string, (int)instrumentInfo.broker, (String)instrumentInfo.description, (double)instrumentInfo.pointValue, (double)instrumentInfo.tickSize, (double)instrumentInfo.tickStep, (double)instrumentInfo.defaultSpread, (double)instrumentInfo.defaultSlippage, (double)0.0, (String)instrumentInfo.commissions, (byte)((byte)instrumentInfo.dataType), (String)instrumentInfo.exchange, (String)instrumentInfo.country, (String)instrumentInfo.sector, (String)instrumentInfo.swap, (double)instrumentInfo.orderSizeMultiplier, (double)instrumentInfo.orderSizeStep);
        InstrumentInfo instrumentInfo2 = InstrumentManager.getInstrumentInfo((String)string);
        try {
            SQWebSocketManager.addToDataQueue(WSDataObjects.getInstruments(), "SQUANT", "QDM", "AlgoWizard");
        }
        catch (Exception exception) {
            Log.error("Cannot send data Websocket message. ", (Throwable)exception);
        }
        return instrumentInfo2;
    }

    private BrokerDto createBroker(BrokerDto brokerDto) throws Exception, DataException {
        String string = brokerDto.getName();
        while (BrokerManager.getInstance().checkBrokerExists(string)) {
            string = DataManager.generateName((String)string);
        }
        BrokerDto brokerDto2 = new BrokerDto();
        brokerDto2.setName(string);
        brokerDto2.setDesc(brokerDto.getName());
        brokerDto2.setMtTimezone(brokerDto.getMtTimezone());
        brokerDto2.setMtUse(brokerDto.isMtUse());
        brokerDto2.setPostfix(brokerDto.getPostfix());
        brokerDto2.setStockPickerUse(brokerDto.isStockPickerUse());
        BrokerManager.getInstance().saveBroker(brokerDto2);
        try {
            SQWebSocketManager.addToDataQueue(WSDataObjects.getBrokers(), "SQUANT", "QDM", "AlgoWizard");
        }
        catch (Exception exception) {
            Log.error("Cannot send data Websocket message. ", (Throwable)exception);
        }
        return brokerDto2;
    }

    private void copy(DataInfo dataInfo, DataBinReaderNew dataBinReaderNew, DataBinWriterNew dataBinWriterNew, String string) throws Exception {
        this.dateFrom = -1L;
        this.records = 0;
        int n = 1000;
        if (dataInfo.rows != 0) {
            n = dataInfo.rows / 10;
        }
        while (dataBinReaderNew.readData()) {
            VersatileData versatileData = dataBinReaderNew.tickData;
            dataBinWriterNew.writeData(versatileData);
            if (this.dateFrom == -1L) {
                this.dateFrom = versatileData.time;
            }
            this.dateTo = versatileData.time;
            ++this.records;
            if (this.cancel) break;
            if (this.records % n != 0) continue;
            this.updateMessage(string + " " + SQTime.toDateString((long)versatileData.time));
        }
    }

    private DataBinReaderNew getDataReader(DataInfo dataInfo, boolean bl) throws Exception {
        boolean bl2 = dataInfo.timeframe.equals("TICK");
        DataBinReaderNew dataBinReaderNew = null;
        dataBinReaderNew = bl2 ? DataBinReaderNew.getInstance((int)2, (InstrumentInfo)dataInfo.symbolInfo) : DataBinReaderNew.getInstance((int)1, (InstrumentInfo)dataInfo.symbolInfo);
        String string = bl ? "unadjusted" : "";
        String string2 = DataManager.getSymbolFolderName((String)this.dataRoot, (String)"History", (String)dataInfo.symbol, (DataInfo)dataInfo);
        File file = new File(string2, DataManager.fixFilename((String)(dataInfo.symbol + string + "_" + dataInfo.timeframe + ".dat")));
        if (!this.publicData && !this.freeSymbol) {
            dataBinReaderNew.setPassword(this.license);
        }
        dataBinReaderNew.setFileName(file.getAbsolutePath());
        dataBinReaderNew.openFile();
        return dataBinReaderNew;
    }

    private List<InstrumentInfo> readInstruments() throws Exception {
        LinkedList<InstrumentInfo> linkedList = new LinkedList<InstrumentInfo>();
        try (Connection connection = this.oldDatabase.getConnection();
             Statement statement = connection.createStatement();
             ResultSet resultSet = statement.executeQuery("SELECT * FROM INSTRUMENTS");){
            while (resultSet.next()) {
                InstrumentInfo instrumentInfo = new InstrumentInfo();
                instrumentInfo.instrument = resultSet.getString("INSTRUMENT").intern();
                instrumentInfo.description = resultSet.getString("DESCRIPTION").intern();
                instrumentInfo.pointValue = resultSet.getDouble("POINTVALUE");
                instrumentInfo.tickSize = resultSet.getDouble("TICKSIZE");
                instrumentInfo.tickStep = resultSet.getDouble("TICKSTEP");
                instrumentInfo.defaultSpread = resultSet.getDouble("DEFAULTSPREAD");
                instrumentInfo.defaultSlippage = resultSet.getDouble("DEFAULTSLIPPAGE");
                instrumentInfo.commissions = resultSet.getString("COMMISSIONS");
                instrumentInfo.dataType = resultSet.getInt("DATATYPE");
                instrumentInfo.exchange = resultSet.getString("EXCHANGE");
                instrumentInfo.country = resultSet.getString("COUNTRY");
                instrumentInfo.sector = resultSet.getString("SECTOR");
                instrumentInfo.decimals = SQUtils.getDecimalPlaces((double)instrumentInfo.tickStep);
                instrumentInfo.swap = resultSet.getString("SWAP");
                instrumentInfo.broker = resultSet.getInt("BROKER_ID");
                try {
                    instrumentInfo.orderSizeMultiplier = resultSet.getDouble("ORDERSIZEMULTIPLIER");
                }
                catch (Exception exception) {
                    instrumentInfo.orderSizeMultiplier = 1.0;
                }
                try {
                    instrumentInfo.orderSizeStep = resultSet.getDouble("ORDERSIZESTEP");
                }
                catch (Exception exception) {
                    instrumentInfo.orderSizeStep = 1.0;
                }
                linkedList.add(instrumentInfo);
            }
        }
        return linkedList;
    }

    private List<BrokerDto> readBrokers() throws Exception {
        LinkedList<BrokerDto> linkedList = new LinkedList<BrokerDto>();
        try (Connection connection = this.oldDatabase.getConnection();
             Statement statement = connection.createStatement();
             ResultSet resultSet = statement.executeQuery("SELECT * FROM BROKER");){
            while (resultSet.next()) {
                BrokerDto brokerDto = new BrokerDto();
                brokerDto.setId(Integer.valueOf(resultSet.getInt("ID")));
                brokerDto.setName(resultSet.getString("NAME"));
                brokerDto.setDesc(resultSet.getString("DESC"));
                brokerDto.setSystem(resultSet.getBoolean("SYSTEM"));
                brokerDto.setMtTimezone(resultSet.getString("MT_TIMEZONE"));
                brokerDto.setMtUse(resultSet.getInt("MT_USE") == 1);
                brokerDto.setStockPickerUse(resultSet.getInt("STOCKPICKER_USE") == 1);
                brokerDto.setPostfix(resultSet.getString("POSTFIX"));
                linkedList.add(brokerDto);
            }
        }
        return linkedList;
    }

    private List<DataInfo> readTickers() throws Exception {
        LinkedList<DataInfo> linkedList = new LinkedList<DataInfo>();
        try (Connection connection = this.oldDatabase.getConnection();
             Statement statement = connection.createStatement();
             ResultSet resultSet = statement.executeQuery("SELECT * FROM DATA");){
            while (resultSet.next()) {
                DataInfo dataInfo = new DataInfo();
                dataInfo.id = resultSet.getInt("ID");
                dataInfo.connection = resultSet.getString("CONNECTION");
                dataInfo.symbol = resultSet.getString("SYMBOL");
                dataInfo.instrument = resultSet.getString("INSTRUMENT");
                dataInfo.timeframe = resultSet.getString("TIMEFRAME");
                dataInfo.timezone = resultSet.getString("TIMEZONE");
                dataInfo.filename = resultSet.getString("FILENAME");
                dataInfo.dateFrom = resultSet.getLong("DATEFROM");
                dataInfo.dateTo = resultSet.getLong("DATETO");
                dataInfo.rows = resultSet.getInt("ROWS");
                dataInfo.secondsRecords = resultSet.getLong("SECONDS_RECORDS");
                dataInfo.barTimeType = resultSet.getInt("DATATYPE");
                dataInfo.decimals = resultSet.getInt("DECIMALS");
                dataInfo.source = resultSet.getInt("SOURCE");
                dataInfo.sourceDataId = resultSet.getInt("SOURCEDATA_ID");
                dataInfo.uSymbol = resultSet.getString("USYMBOL");
                dataInfo.uSymbolName = resultSet.getString("USYMBOLNAME");
                dataInfo.show = resultSet.getBoolean("SHOW");
                dataInfo.basketId = resultSet.getInt("BASKET_ID");
                dataInfo.brokerId = resultSet.getInt("BROKER_ID");
                String string = dataInfo.timeframe = dataInfo.timeframe == null || dataInfo.timeframe.equals("null") ? null : dataInfo.timeframe;
                if (dataInfo.symbol.startsWith("[") || dataInfo.symbol.contains("_limited") || dataInfo.symbol.contains("SPY_benchmark")) continue;
                linkedList.add(dataInfo);
            }
        }
        return linkedList;
    }

    private void openDatabase() {
        String string = this.path + File.separator + "user" + File.separator + "data";
        this.oldDatabase = new DataDb(string){

            public void initDatabase() {
            }
        };
    }

    public String validate() {
        if (!new File(this.dataRoot).exists()) {
            return L.t((String)"Not found path on your disk: %s", (Object[])new Object[]{this.dataRoot});
        }
        return null;
    }

    public void cancel() {
        this.cancel = true;
    }
}

