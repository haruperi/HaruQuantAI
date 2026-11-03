/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.DataFolderSweeper
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.StockGroupUpdateErrorManager
 *  com.strategyquant.datalib.historyData.TickerFilterDto
 *  com.strategyquant.datalib.historyData.dto.TickerDto
 *  com.strategyquant.datalib.historyData.dto.TickerKind
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.datalib.timezone.Timezone
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.gridlib.client.IGridMessageListener
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.historyData.DataSources
 *  com.strategyquant.lib.historyData.HistoryDataSubscription
 *  com.strategyquant.lib.tempfiles.TempFilesManager
 *  org.apache.http.client.ClientProtocolException
 *  org.apache.http.client.config.RequestConfig
 *  org.apache.http.client.methods.CloseableHttpResponse
 *  org.apache.http.client.methods.HttpGet
 *  org.apache.http.client.methods.HttpUriRequest
 *  org.apache.http.impl.client.HttpClientBuilder
 *  org.jdom2.Document
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.jdom2.input.SAXBuilder
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.data.download;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataFolderSweeper;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.StockGroupUpdateErrorManager;
import com.strategyquant.datalib.historyData.TickerFilterDto;
import com.strategyquant.datalib.historyData.dto.TickerDto;
import com.strategyquant.datalib.historyData.dto.TickerKind;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.datalib.timezone.Timezone;
import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.historyData.DataSources;
import com.strategyquant.lib.historyData.HistoryDataSubscription;
import com.strategyquant.lib.tempfiles.TempFilesManager;
import com.strategyquant.tradinglib.crypto.CryptoDownloadJob;
import com.strategyquant.tradinglib.darwinex.DarwinexImportManager;
import com.strategyquant.tradinglib.data.download.IDownloadDispatcher;
import com.strategyquant.tradinglib.data.download.NotDownloadableDataException;
import com.strategyquant.tradinglib.data.download.Queue;
import com.strategyquant.tradinglib.dukascopy.CdnInfo;
import com.strategyquant.tradinglib.dukascopy.DukasImportManager;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.historyData.DownloadEodStockHistorySymbolJob;
import com.strategyquant.tradinglib.historyData.DownloadHistorySymbolJob;
import com.strategyquant.tradinglib.historyData.EodHistoryDataCache;
import com.strategyquant.tradinglib.historyData.HistoryDataManager;
import com.strategyquant.tradinglib.mt5api.Mt5ApiDownloaderJob;
import com.strategyquant.tradinglib.mt5api.Mt5ApiImportInfo;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.tradinglib.yahoo.YahooDownloadJob;
import java.io.File;
import java.io.IOException;
import java.net.UnknownHostException;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.locks.ReentrantLock;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.config.RequestConfig;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.impl.client.HttpClientBuilder;
import org.jdom2.Document;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.jdom2.input.SAXBuilder;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DownloadDispatcher
implements IDownloadDispatcher {
    private static final int BATCH_UPDATE = 10;
    private static final long MIN_SYNC_UI_DELTA = 1500L;
    private long lastSync;
    private List<JSONObject> symbolsForUpdate = new LinkedList<JSONObject>();
    private IGridMessageListener gridFinishListener = new IGridMessageListener(){

        public void messageReceived(GridMessage gridMessage) {
            if (gridMessage.getMessageID() == 1) {
                String string = gridMessage.getJobDetails().getJobID();
                String string2 = string.substring(DownloadDispatcher.JOB_PREFIX.length());
                DownloadDispatcher.this.downloadFinished(string2);
                DownloadDispatcher.this.jobsFinished++;
                DownloadDispatcher.this.updateTotal();
                DownloadDispatcher.this.tryToRunDownload();
                DownloadDispatcher.this.updateUI(string2);
                if (!(DownloadDispatcher.this.commonQueue.isBusy() || DownloadDispatcher.this.cdnQueue.isBusy() || DownloadDispatcher.this.skipReset)) {
                    DownloadDispatcher.this.jobsFinished = 0;
                    DownloadDispatcher.this.jobsToBeHandled = 0;
                }
                if (!DownloadDispatcher.this.commonQueue.isBusy() && !DownloadDispatcher.this.cdnQueue.isBusy()) {
                    DownloadDispatcher.this.finishBatch();
                }
            }
            for (int i = 0; i < DownloadDispatcher.this.extraListeners.size(); ++i) {
                ((IGridMessageListener)DownloadDispatcher.this.extraListeners.get(i)).messageReceived(gridMessage);
            }
        }
    };
    public static final String NEW_CDN_USER = "cdnuser";
    public static final String NEW_CDN_PASS = "QmwwrOrdxKK52pPUmjkf";
    private static final String DARWINEX_CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/darwinex";
    private static final String DARWINEX_HK_BASE_CDN_URL = "https://cdn005.strategyquantcdn.com/data/darwinex";
    private static final String DUKASCOPY_CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/dukascopy";
    private static final String DUKASCOPY_HK_BASE_CDN_URL = "https://cdn005.strategyquantcdn.com/data/dukascopy";
    public static final String SYMBOL_TOTAL = "TotalProgressSymbol";
    public static final String JOB_PREFIX = "downloadjob_";
    private static final Logger Log = LoggerFactory.getLogger(DownloadDispatcher.class);
    private static final int TIMEOUT = 10;
    private static DownloadDispatcher instance = new DownloadDispatcher();
    private Queue commonQueue = new Queue(this);
    private Queue cdnQueue = new Queue(this);
    private Set<String> cryptoExchangeDownload = new HashSet<String>();
    private AtomicBoolean mt5apiDownload = new AtomicBoolean(false);
    private ReentrantLock lock = new ReentrantLock(true);
    private ArrayList<IGridMessageListener> extraListeners = new ArrayList();
    private MultiProgressListener totalListener = DataManagerDataProgress.get().createListener("TotalProgressSymbol", "");
    private volatile int jobsFinished = 0;
    private volatile int jobsToBeHandled = 0;
    private volatile boolean skipReset = false;
    private boolean newCdn = false;
    private String customDukascopyBaseCdnUrl;
    private String customDarwinexBaseCdnUrl;

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void updateUI(String string) {
        block6: {
            try {
                if (MainApp.runInConsole()) break block6;
                boolean bl = !this.commonQueue.isBusy() && !this.cdnQueue.isBusy();
                List<JSONObject> list = this.symbolsForUpdate;
                synchronized (list) {
                    this.symbolsForUpdate.add(this.getSymbolInfo(string));
                    long l = System.currentTimeMillis() - this.lastSync;
                    if (bl || this.symbolsForUpdate.size() % 10 == 0 && l > 1500L) {
                        this.sendUpdateUI();
                    }
                }
            }
            catch (Exception exception) {
                Log.error("Error while updating UI", (Throwable)exception);
            }
        }
    }

    private JSONObject getSymbolInfo(String string) throws DataException {
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string);
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("symbol", (Object)dataInfo.symbol);
        jSONObject.put("barType", dataInfo.barTimeType);
        jSONObject.put("dateFrom", dataInfo.dateFrom);
        jSONObject.put("dateTo", dataInfo.dateTo);
        jSONObject.put("rows", dataInfo.rows);
        jSONObject.put("totalDays", SQTime.getDaysBetween((long)dataInfo.dateFrom, (long)dataInfo.dateTo));
        jSONObject.put("connection", (Object)dataInfo.connection);
        jSONObject.put("filename", (Object)dataInfo.filename);
        jSONObject.put("instrument", (Object)dataInfo.instrument);
        jSONObject.put("timeframe", (Object)dataInfo.timeframe);
        jSONObject.put("timezone", (Object)Timezone.print((String)dataInfo.timezone, (int)dataInfo.source, (boolean)false));
        jSONObject.put("timezoneShort", (Object)Timezone.print((String)dataInfo.timezone, (int)dataInfo.source, (boolean)true));
        jSONObject.put("source", dataInfo.source);
        jSONObject.put("secondsRecords", dataInfo.secondsRecords);
        InstrumentInfo instrumentInfo = InstrumentManager.getInstrumentInfo((String)dataInfo.instrument);
        jSONObject.put("pointValue", instrumentInfo.pointValue);
        jSONObject.put("tickSize", instrumentInfo.tickSize);
        jSONObject.put("tickStep", instrumentInfo.tickStep);
        jSONObject.put("dataType", instrumentInfo.dataType);
        jSONObject.put("spread", instrumentInfo.defaultSpread);
        jSONObject.put("slippage", instrumentInfo.defaultSlippage);
        jSONObject.put("commissions", (Object)instrumentInfo.commissions);
        jSONObject.put("swap", (Object)instrumentInfo.swap);
        jSONObject.put("uSymbol", (Object)dataInfo.uSymbol);
        jSONObject.put("uSymbolName", (Object)dataInfo.uSymbolName);
        jSONObject.put("id", dataInfo.id);
        jSONObject.put("sourceDataId", dataInfo.sourceDataId);
        jSONObject.put("show", dataInfo.show);
        jSONObject.put("broker", instrumentInfo.broker);
        jSONObject.put("brokerName", (Object)BrokerManager.getInstance().getBrokerName(instrumentInfo.broker));
        return jSONObject;
    }

    public boolean isEmpty() {
        return !this.cdnQueue.isBusy() && !this.commonQueue.isBusy();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void sendUpdateUI() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("action", (Object)"download_single");
        List<JSONObject> list = this.symbolsForUpdate;
        synchronized (list) {
            jSONObject.put("data", (Object)new JSONArray((Object)this.symbolsForUpdate.toArray()));
            this.symbolsForUpdate.clear();
            this.lastSync = System.currentTimeMillis();
        }
        SQWebSocketManager.addToDataQueue(new DataToSend("data", jSONObject), "SQUANT", "QDM", "AlgoWizard");
    }

    private void finishBatch() {
        DataManager.flushUpdatedData();
        if (BasketOfStocksManager.getInstance() != null) {
            BasketOfStocksManager.getInstance().updateGroupsOfSymbols();
            SQWebSocketManager.addToDataQueue(WSDataObjects.getBaskets(), "SQUANT", "QDM", "AlgoWizard");
            this.sendStockGroupErrorsToUI();
        }
        try {
            if (!MainApp.runInConsole()) {
                SQWebSocketManager.addToDataQueue(WSDataObjects.getData("", "download"), "SQUANT", "QDM", "AlgoWizard");
            }
        }
        catch (Exception exception) {
            Log.error("Error while updating UI", (Throwable)exception);
        }
    }

    private void sendStockGroupErrorsToUI() {
        String string = this.getDownloadGroupSummaryError();
        if (string == null) {
            return;
        }
        this.totalListener.setMessage(string);
    }

    private String getDownloadGroupSummaryError() {
        Object object;
        BasketDto basketDto;
        Object object22;
        Map map = StockGroupUpdateErrorManager.getInstance().finished();
        if (map == null) {
            return null;
        }
        Set set = map.keySet();
        HashMap<Object, LinkedList<String>> hashMap = new HashMap<Object, LinkedList<String>>();
        for (Object object22 : set) {
            Object object3 = BasketOfStocksManager.getInstance().getGroupsForStock((String)object22);
            if (object3 == null) continue;
            basketDto = object3.iterator();
            while (basketDto.hasNext()) {
                object = (Integer)basketDto.next();
                LinkedList<String> linkedList = (LinkedList<String>)hashMap.get(object);
                if (linkedList == null) {
                    linkedList = new LinkedList<String>();
                    hashMap.put(object, linkedList);
                }
                linkedList.add((String)map.get(object22));
            }
        }
        if (hashMap.isEmpty()) {
            return null;
        }
        StringBuilder stringBuilder = new StringBuilder();
        for (Object object3 : hashMap.keySet()) {
            basketDto = BasketOfStocksManager.getInstance().getBasket((Integer)object3);
            object = (List)hashMap.get(object3);
            stringBuilder.append("Updated group " + basketDto.getName() + ", " + object.size() + " error" + (object.size() > 1 ? "s" : "") + System.lineSeparator());
            for (int i = 0; i < object.size(); ++i) {
                String string = (String)object.get(i);
                stringBuilder.append(string);
                stringBuilder.append(System.lineSeparator());
            }
        }
        object22 = stringBuilder.toString();
        object22 = ((String)object22).trim().replace(System.lineSeparator(), "<br>");
        return object22;
    }

    public DownloadDispatcher() {
        File file = new File(MainApp.getDataPath() + File.separator + "user", "cdn.txt");
        if (file.exists()) {
            try {
                List<String> list = Files.readAllLines(file.toPath());
                this.customDukascopyBaseCdnUrl = list.get(0).trim();
                this.customDarwinexBaseCdnUrl = list.get(1).trim();
            }
            catch (Exception exception) {
                Log.error("Error while loading cdn.txt content", (Throwable)exception);
            }
        }
    }

    private boolean useHkServer() {
        String string = MainApp.settings().get("cdnPreferred", DataSources.DOWNLOAD_TYPE_CDN);
        return DataSources.DOWNLOAD_TYPE_CDN_CN.equals(string);
    }

    private String getDarwinexBaseUrl() {
        if (this.customDarwinexBaseCdnUrl != null) {
            return this.customDarwinexBaseCdnUrl;
        }
        if (this.useHkServer()) {
            return DARWINEX_HK_BASE_CDN_URL;
        }
        return DARWINEX_CDN_BASE_URL;
    }

    private String getDukascopyBaseUrl(ImportInfo importInfo) {
        String string;
        if (!importInfo.useCDN) {
            return null;
        }
        String string2 = string = importInfo.downloadM1Data ? "m1" : "tick";
        if (this.customDukascopyBaseCdnUrl != null) {
            return this.customDukascopyBaseCdnUrl + "/" + string;
        }
        if (DataSources.DOWNLOAD_TYPE_CDN_CN.equals(importInfo.downloadType)) {
            return "https://cdn005.strategyquantcdn.com/data/dukascopy/" + string;
        }
        return "https://cdn.strategyquantcdn.com/data/dukascopy/" + string;
    }

    private void updateTotal() {
        try {
            Log.debug("Total updating");
            this.lock.lock();
            double d = 0.0;
            if (this.jobsToBeHandled != 0) {
                d = (double)this.jobsFinished / (double)this.jobsToBeHandled;
            } else if (this.jobsFinished > 0) {
                d = 1.0;
            }
            this.totalListener.setMessage(this.jobsFinished + " / " + this.jobsToBeHandled);
            this.totalListener.onProgress(d * 100.0);
        }
        finally {
            this.lock.unlock();
        }
        Log.debug("Total updated");
    }

    private void tryToRunDownload() {
        this.commonQueue.tryToRunDownload();
        this.cdnQueue.tryToRunDownload();
    }

    @Override
    public boolean isMt5DownloadExecuted() {
        return this.mt5apiDownload.get();
    }

    private CdnInfo readDukascopyCdnInfos(String string) throws ClientProtocolException, IOException, IllegalStateException, JDOMException {
        CdnInfo cdnInfo = new CdnInfo();
        RequestConfig requestConfig = RequestConfig.custom().setConnectTimeout(10000).setConnectionRequestTimeout(10000).setSocketTimeout(10000).build();
        CloseableHttpResponse closeableHttpResponse = null;
        try {
            closeableHttpResponse = HttpClientBuilder.create().setDefaultRequestConfig(requestConfig).build().execute((HttpUriRequest)new HttpGet(string));
        }
        catch (UnknownHostException unknownHostException) {
            Log.error("Error while downloade descriptor. Unknown host: " + string, (Throwable)unknownHostException);
            throw new RuntimeException("The server address could not be resolved. This may be due to a DNS or network issue.");
        }
        closeableHttpResponse.getEntity().getContent();
        SAXBuilder sAXBuilder = new SAXBuilder();
        Document document = null;
        try {
            document = sAXBuilder.build(closeableHttpResponse.getEntity().getContent());
        }
        catch (Exception exception) {
            Log.error("Error while parse CDN descriptor: " + string, (Throwable)exception);
            throw new RuntimeException("Error while downloading and parsing descriptor XML.");
        }
        Element element = document.getRootElement();
        List list = element.getChildren("data");
        for (Element element2 : list) {
            String string2 = element2.getAttributeValue("symbol");
            String string3 = element2.getAttributeValue("url");
            String string4 = element2.getAttributeValue("format");
            String string5 = element2.getAttributeValue("tf");
            cdnInfo.addSymbolInfo(string2, string5, string3, string4);
            Log.debug("CDN metadata added: {}, timeframe:{}, url:{}", new Object[]{string2, string5, string3});
        }
        return cdnInfo;
    }

    public static DownloadDispatcher get() {
        return instance;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void updateHistoryData(List<DataInfo> list, Map<String, TickerDto> map) throws Exception {
        try {
            this.skipReset = true;
            this.lock.lock();
            boolean bl = false;
            for (DataInfo dataInfo : list) {
                TickerDto tickerDto = map.get(dataInfo.uSymbol);
                this.testSubscriptions(dataInfo, tickerDto);
                if (tickerDto == null || dataInfo.sourceDataId != 0) continue;
                boolean bl2 = this.registerUpdate(dataInfo, tickerDto, null, true);
                bl = bl2 || bl;
            }
            if (!(bl || this.commonQueue.isBusy() || this.cdnQueue.isBusy())) {
                this.sendStockGroupErrorsToUI();
            }
        }
        finally {
            this.skipReset = false;
            this.lock.unlock();
        }
        this.cdnQueue.tryToRunDownload();
    }

    private void testSubscriptions(DataInfo dataInfo, TickerDto tickerDto) {
        boolean bl;
        String string = dataInfo.timeframe;
        boolean bl2 = bl = !string.equals("M1");
        if (dataInfo.source == 5 && !HistoryDataSubscription.getInstance().isAllowedEquity(dataInfo.uSymbol, bl)) {
            throw new RuntimeException(L.t((String)"You don't have subscriptions for requested data.", (Object[])new Object[0]));
        }
        if (dataInfo.source == 6 && !HistoryDataSubscription.getInstance().isAllowedFuture(dataInfo.uSymbol, tickerDto.getMarketName(), bl)) {
            throw new RuntimeException(L.t((String)"You don't have subscriptions for requested data.", (Object[])new Object[0]));
        }
    }

    public void updateHistoryData(DataInfo dataInfo, TickerDto tickerDto) throws Exception {
        try {
            this.lock.lock();
            if (tickerDto == null) {
                Log.info("Can't download {}. Ticker definition was not found. Ticker was probably removed from central database.", (Object)dataInfo.symbol);
            }
            if (tickerDto != null && dataInfo.sourceDataId == 0) {
                this.testSubscriptions(dataInfo, tickerDto);
                this.registerUpdate(dataInfo, tickerDto, null, true);
            }
        }
        finally {
            this.lock.unlock();
        }
        this.cdnQueue.tryToRunDownload();
    }

    private boolean registerUpdate(DataInfo dataInfo, TickerDto tickerDto, ImportInfo importInfo, boolean bl) throws Exception {
        if (bl && this.cdnQueue.exists(dataInfo.symbol) || !bl && this.commonQueue.exists(dataInfo.symbol)) {
            Log.debug("Symbol is already in queue or running: {}", (Object)dataInfo.symbol);
            return false;
        }
        TickerDto tickerDto2 = tickerDto;
        if (tickerDto != null && tickerDto.getAliasTickerId() != null) {
            TickerDto tickerDto3;
            boolean bl2 = dataInfo.source == 5;
            TickerDto tickerDto4 = tickerDto3 = bl2 ? HistoryDataManager.get().getStockTicker(tickerDto.getAliasTickerId()) : HistoryDataManager.get().getFutureTicker(tickerDto.getAliasTickerId());
            if (tickerDto3 != null) {
                tickerDto2 = tickerDto3;
            }
        }
        if (tickerDto2 != null && tickerDto2.getDateTo().getTime() <= dataInfo.dateTo) {
            ++this.jobsToBeHandled;
            ++this.jobsFinished;
            this.updateTotal();
            return false;
        }
        Details details = new Details();
        details.ticker = tickerDto;
        details.importInfo = importInfo;
        details.symbol = dataInfo.symbol;
        details.dataInfo = dataInfo;
        details.listener = DownloadDispatcher.createListener(dataInfo);
        details.listener.onProgress(0.1);
        details.listener.setMessage(L.t((String)"Waiting in queue", (Object[])new Object[0]));
        if (bl) {
            this.cdnQueue.register(dataInfo.symbol, details);
        } else {
            this.commonQueue.register(dataInfo.symbol, details);
        }
        Log.debug("Symbol: {} registered for download.", (Object)dataInfo.symbol);
        ++this.jobsToBeHandled;
        this.updateTotal();
        return true;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void update(DataInfo dataInfo, ImportInfo importInfo) throws Exception {
        boolean bl = false;
        try {
            this.lock.lock();
            bl = this.registerUpdate(dataInfo, null, importInfo, importInfo.useCDN);
        }
        finally {
            this.lock.unlock();
        }
        if (bl) {
            this.tryToRunDownload();
        }
    }

    public static DataManagerProgressListener createListener(DataInfo dataInfo) throws Exception {
        String string = null;
        switch (dataInfo.source) {
            case 5: {
                string = "sqEquityData/updateDataAction";
                break;
            }
            case 6: {
                string = "sqFuturesData/updateDataAction";
                break;
            }
            case 3: {
                string = "dataSourceYahoo/importDataAction";
                break;
            }
            case 7: {
                string = "dataSourceCrypto/importDataAction";
                break;
            }
            case 2: {
                string = "dataSourceDukascopy/importDataAction";
                break;
            }
            case 4: {
                string = "darwinex/downloadDataAction";
                break;
            }
            case 8: {
                string = "dataSourceMt5Api/downloadDataAction";
                break;
            }
            default: {
                throw new NotDownloadableDataException("Not supported datasource: " + dataInfo.source);
            }
        }
        return (DataManagerProgressListener)DataManagerDataProgress.get().createListener(dataInfo.symbol, string);
    }

    public void setQueueSizes(int n, int n2) {
        this.lock.lock();
        boolean bl = this.commonQueue.setQueueSize(n);
        boolean bl2 = this.cdnQueue.setQueueSize(n2);
        this.lock.unlock();
        if (bl2) {
            this.cdnQueue.tryToRunDownload();
        }
        if (bl) {
            this.commonQueue.tryToRunDownload();
        }
    }

    public int getQueueSize() {
        return this.commonQueue.getQueueSize();
    }

    @Override
    public boolean isCryptoExchangeDownload(String string) {
        return this.cryptoExchangeDownload.contains(string);
    }

    @Override
    public void extecuteDownloadJob(Details details) throws Exception {
        int n = details.dataInfo.source;
        try {
            if (n == 5 || n == 6) {
                this.executeHistoryDownload(details);
            } else if (n == 2) {
                this.executeDukascopyDownload(details);
            } else if (n == 4) {
                this.executeDarwinexDownload(details);
            } else if (n == 3) {
                this.executeYahooDownload(details);
            } else if (n == 7) {
                this.executeCryptoDownload(details);
            } else if (n == 8) {
                this.executeMt5Download(details);
            }
            DataFolderSweeper.get().setSkip(true);
            TempFilesManager.get().setAutoDeleteEnabled(false);
            Log.debug("Executed download for: {}", (Object)details.symbol);
        }
        catch (Exception exception) {
            ++this.jobsFinished;
            throw exception;
        }
    }

    private void executeMt5Download(Details details) throws Exception {
        String string = DownloadDispatcher.getJobIdent(details.dataInfo.symbol);
        Mt5ApiDownloaderJob mt5ApiDownloaderJob = new Mt5ApiDownloaderJob(string, details.listener, details.dataInfo, (Mt5ApiImportInfo)details.importInfo);
        this.registerListener(string);
        this.mt5apiDownload.set(true);
        SQGrid.getGridClient().executeOnGrid(string, (GridJob)mt5ApiDownloaderJob);
    }

    private void executeCryptoDownload(Details details) throws Exception {
        String string = DownloadDispatcher.getJobIdent(details.dataInfo.symbol);
        CryptoDownloadJob cryptoDownloadJob = new CryptoDownloadJob(string, details.listener, details.dataInfo, details.importInfo);
        this.cryptoExchangeDownload.add(details.dataInfo.uSymbolName);
        this.registerListener(string);
        SQGrid.getGridClient().executeOnGrid(string, (GridJob)cryptoDownloadJob);
    }

    private void executeYahooDownload(Details details) throws Exception {
        String string = DownloadDispatcher.getJobIdent(details.dataInfo.symbol);
        YahooDownloadJob yahooDownloadJob = new YahooDownloadJob(string, details.listener, details.dataInfo, details.importInfo);
        this.registerListener(string);
        SQGrid.getGridClient().executeOnGrid(string, (GridJob)yahooDownloadJob);
    }

    private void executeDukascopyDownload(Details details) throws Exception {
        String string = DownloadDispatcher.getJobIdent(details.dataInfo.symbol);
        String string2 = this.getDukascopyBaseUrl(details.importInfo);
        GridJob gridJob = DukasImportManager.get().importData(string, string2, details.importInfo, details.listener, this.gridFinishListener);
        SQGrid.getGridClient().executeOnGrid(string, gridJob);
    }

    private void registerListener(String string) {
        GridClient gridClient = SQGrid.getGridClient();
        if (gridClient.isRegisteredMessageListener(string)) {
            gridClient.removeMessageListener(string);
        }
        gridClient.registerMessageListener(string, this.gridFinishListener);
    }

    private void executeDarwinexDownload(Details details) throws Exception {
        String string = DownloadDispatcher.getJobIdent(details.dataInfo.symbol);
        String string2 = this.getDarwinexBaseUrl();
        GridJob gridJob = DarwinexImportManager.get().importData(string, string2, details.importInfo, details.listener, this.gridFinishListener);
        SQGrid.getGridClient().executeOnGrid(string, gridJob);
    }

    private void executeHistoryDownload(Details details) throws Exception {
        boolean bl;
        DataInfo dataInfo = details.dataInfo;
        String string = DownloadDispatcher.getJobIdent(dataInfo.symbol);
        TickerFilterDto tickerFilterDto = new TickerFilterDto();
        tickerFilterDto.setSearchInTicker(true);
        tickerFilterDto.setExactMatch(true);
        tickerFilterDto.setNames(new String[]{dataInfo.uSymbol});
        boolean bl2 = bl = dataInfo.source == 5;
        if (bl && details.ticker.isEod()) {
            DownloadEodStockHistorySymbolJob downloadEodStockHistorySymbolJob = new DownloadEodStockHistorySymbolJob(string, dataInfo, bl ? TickerKind.STOCK : TickerKind.FUTURES, details.ticker, false);
            downloadEodStockHistorySymbolJob.setProgressListener(details.listener);
            this.registerListener(string);
            SQGrid.getGridClient().executeOnGrid(string, (GridJob)downloadEodStockHistorySymbolJob);
        } else {
            DownloadHistorySymbolJob downloadHistorySymbolJob = new DownloadHistorySymbolJob(string, dataInfo, bl ? TickerKind.STOCK : TickerKind.FUTURES, details.ticker);
            downloadHistorySymbolJob.setProgressListener(details.listener);
            this.registerListener(string);
            SQGrid.getGridClient().executeOnGrid(string, (GridJob)downloadHistorySymbolJob);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void downloadFinished(String string) {
        int n;
        int n2;
        try {
            this.lock.lock();
            if (!this.cdnQueue.downloadJobFinished(string)) {
                this.commonQueue.downloadJobFinished(string);
            }
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string);
            if (dataInfo.source == 7) {
                this.cryptoExchangeDownload.remove(dataInfo.uSymbolName);
            } else if (dataInfo.source == 8) {
                this.mt5apiDownload.set(false);
            }
            n2 = this.cdnQueue.getRunningJobsCount() + this.commonQueue.getRunningJobsCount();
            n = this.cdnQueue.getWaitingJobsCount() + this.commonQueue.getWaitingJobsCount();
            if (n2 == 0 && n == 0) {
                TempFilesManager.get().setAutoDeleteEnabled(true);
                EodHistoryDataCache.getInstance().reset();
            }
        }
        finally {
            this.lock.unlock();
        }
        Log.info("Finished: {}, already executed: {}, in queue: {}", new Object[]{string, n2, n});
        SQGrid.getGridClient().removeMessageListener(DownloadDispatcher.getJobIdent(string));
    }

    private String getGridGroup(String string) {
        return DownloadDispatcher.getJobIdent(string);
    }

    @Override
    public void performPause(String string, Details details) {
        if (details != null) {
            details.paused = true;
            details.listener.onPause();
        } else {
            SQGrid.getGridClient().pause(this.getGridGroup(string));
            DataManagerDataProgress.get().createListener(string).onPause();
        }
        Log.debug("Paused symbol: {}", (Object)string);
    }

    @Override
    public void performResume(String string, Details details) {
        if (details != null) {
            details.paused = false;
            details.listener.onContinue();
        } else {
            SQGrid.getGridClient().restart(this.getGridGroup(string));
            DataManagerDataProgress.get().createListener(string).onContinue();
        }
        Log.debug("Resumed symbol: {}", (Object)string);
    }

    @Override
    public void performStop(String string, Details details) {
        if (details != null) {
            details.listener.onProgress(100.0);
            details.listener.setMessage(L.t((String)"Stopped", (Object[])new Object[0]));
            ++this.jobsFinished;
        } else {
            SQGrid.getGridClient().stop(this.getGridGroup(string));
        }
        Log.debug("Stopped symbol: {}", (Object)string);
    }

    public static String getJobIdent(String string) {
        String string2 = JOB_PREFIX + string;
        return string2;
    }

    public void stopAll() {
        try {
            this.lock.lock();
            this.commonQueue.stopAll();
            this.cdnQueue.stopAll();
            this.jobsFinished = this.jobsToBeHandled;
        }
        finally {
            this.lock.unlock();
        }
        DataManager.flushUpdatedData();
        this.updateTotal();
    }

    public void stop(String string) {
        try {
            this.lock.lock();
            Details details = this.removeFromDownloadQueue(string);
            this.performStop(string, details);
        }
        finally {
            this.lock.unlock();
        }
        this.tryToRunDownload();
        this.updateTotal();
    }

    private Details removeFromDownloadQueue(String string) {
        Details details = this.cdnQueue.removeFromDownloadQueue(string);
        if (details != null) {
            return details;
        }
        return this.commonQueue.removeFromDownloadQueue(string);
    }

    private Details getFromDownloadQueue(String string) {
        Details details = this.cdnQueue.getFromDownloadQueue(string);
        if (details != null) {
            return details;
        }
        return this.commonQueue.getFromDownloadQueue(string);
    }

    public void pauseAll() {
        try {
            this.lock.lock();
            this.commonQueue.pauseAll();
            this.cdnQueue.pauseAll();
        }
        finally {
            this.lock.unlock();
            Log.debug("Paused all");
        }
    }

    public void pause(String string) {
        try {
            this.lock.lock();
            Details details = this.getFromDownloadQueue(string);
            this.performPause(string, details);
        }
        finally {
            this.lock.unlock();
        }
    }

    public void resumeAll() {
        try {
            this.lock.lock();
            this.commonQueue.resumeAll();
            this.cdnQueue.resumeAll();
        }
        finally {
            this.lock.unlock();
            Log.debug("Resumed all");
        }
        this.tryToRunDownload();
    }

    public void resume(String string) {
        try {
            this.lock.lock();
            Details details = this.getFromDownloadQueue(string);
            this.performResume(string, details);
        }
        finally {
            this.lock.unlock();
        }
    }

    public void addExtraListener(IGridMessageListener iGridMessageListener) {
        this.extraListeners.add(iGridMessageListener);
    }

    public void removeExtraListener(IGridMessageListener iGridMessageListener) {
        this.extraListeners.remove(iGridMessageListener);
    }

    static class Details {
        public String symbol;
        public DataInfo dataInfo;
        public DataManagerProgressListener listener;
        public boolean paused = false;
        public TickerDto ticker;
        public ImportInfo importInfo;

        Details() {
        }
    }
}

