/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.historyData.AbstractHistoryDataDao
 *  com.strategyquant.datalib.historyData.FuturesHistoryDataDao
 *  com.strategyquant.datalib.historyData.StockHistoryDataDao
 *  com.strategyquant.datalib.historyData.TickerFilterDto
 *  com.strategyquant.datalib.historyData.TickerRenameInfo
 *  com.strategyquant.datalib.historyData.dto.CommodityDto
 *  com.strategyquant.datalib.historyData.dto.TickerDto
 *  com.strategyquant.datalib.historyData.dto.TickerKind
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.L88OaFjjon.V571hfnsHw
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.exception.SQException
 *  com.strategyquant.lib.historyData.DataSources
 *  com.strategyquant.lib.hw.HardwareInfo
 *  com.strategyquant.model.IdName
 *  org.apache.commons.io.IOUtils
 *  org.apache.http.HttpEntity
 *  org.apache.http.client.ClientProtocolException
 *  org.apache.http.client.entity.UrlEncodedFormEntity
 *  org.apache.http.client.methods.CloseableHttpResponse
 *  org.apache.http.client.methods.HttpGet
 *  org.apache.http.client.methods.HttpPost
 *  org.apache.http.client.methods.HttpUriRequest
 *  org.apache.http.conn.ConnectTimeoutException
 *  org.apache.http.impl.client.CloseableHttpClient
 *  org.apache.http.message.BasicNameValuePair
 *  org.jdom2.JDOMException
 *  org.joda.time.format.DateTimeFormat
 *  org.joda.time.format.DateTimeFormatter
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.historyData;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.historyData.AbstractHistoryDataDao;
import com.strategyquant.datalib.historyData.FuturesHistoryDataDao;
import com.strategyquant.datalib.historyData.StockHistoryDataDao;
import com.strategyquant.datalib.historyData.TickerFilterDto;
import com.strategyquant.datalib.historyData.TickerRenameInfo;
import com.strategyquant.datalib.historyData.dto.CommodityDto;
import com.strategyquant.datalib.historyData.dto.TickerDto;
import com.strategyquant.datalib.historyData.dto.TickerKind;
import com.strategyquant.lib.L;
import com.strategyquant.lib.L88OaFjjon.V571hfnsHw;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.exception.SQException;
import com.strategyquant.lib.historyData.DataSources;
import com.strategyquant.lib.hw.HardwareInfo;
import com.strategyquant.model.IdName;
import com.strategyquant.tradinglib.historyData.DownloadMessageHandler;
import com.strategyquant.tradinglib.historyData.HttpApacheManager;
import java.io.BufferedOutputStream;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.SocketTimeoutException;
import java.nio.file.Files;
import java.nio.file.StandardOpenOption;
import java.security.NoSuchAlgorithmException;
import java.sql.Date;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import javax.net.ssl.SSLProtocolException;
import org.apache.commons.io.IOUtils;
import org.apache.http.HttpEntity;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.entity.UrlEncodedFormEntity;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.conn.ConnectTimeoutException;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.message.BasicNameValuePair;
import org.jdom2.JDOMException;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class HistoryDataManager {
    public static final Long BMF_ID = 100000L;
    public static final String CDN_USER = "cdnuser";
    public static final String CDN_PASS = "QmwwrOrdxKK52pPUmjkf";
    public static final Logger Log = LoggerFactory.getLogger(HistoryDataManager.class);
    private static final String CDN_BASE_URL = "https://cdn.strategyquantcdn.com/";
    private static final String HK_BASE_CDN_URL = "https://cdn005.strategyquantcdn.com/";
    private static HistoryDataManager instance = null;
    private static final int TIMEOUT = 40;
    private static final int RETRY_COUNT = 5;
    private static final int RETRY_DELAY = 30;
    private String macAddr;
    private String diskSn;
    private boolean devel = false;
    private String customCdnBase;
    private String dataFolder = SQPaths.dataDirPath;
    private FuturesHistoryDataDao futuresDao;
    private StockHistoryDataDao stockDao;
    private long stockDaoBorn;
    private long futureDaoBorn;
    private boolean stockWasChanged;

    private HistoryDataManager() {
        File file = new File(MainApp.getDataPath() + File.separator + "user", "cdn.txt");
        if (file.exists()) {
            try {
                List<String> list = Files.readAllLines(file.toPath());
                if (list.size() > 2) {
                    this.customCdnBase = list.get(2).trim();
                    if (!this.customCdnBase.endsWith("/")) {
                        this.customCdnBase = this.customCdnBase + "/";
                    }
                }
            }
            catch (Exception exception) {
                Log.error("Error while loading cdn.txt content", (Throwable)exception);
            }
        }
        this.macAddr = HardwareInfo.getMacAddress();
        this.diskSn = HardwareInfo.getDiskSN();
        this.checkDevelMode();
    }

    private String getBaseUrl() {
        if (this.customCdnBase != null) {
            return this.customCdnBase;
        }
        if (this.useHkServer()) {
            return HK_BASE_CDN_URL;
        }
        return CDN_BASE_URL;
    }

    private String getVersionUrl(boolean bl) {
        return this.getBaseUrl() + "data/database/" + (bl ? "data_stock.version" : "data_futures.version");
    }

    private String getH2Url(boolean bl) {
        return this.getBaseUrl() + "data/database/" + (bl ? "data_stock.zip" : "data_futures.zip");
    }

    private String getDataUrl() {
        return this.getBaseUrl() + "sqdata.php";
    }

    private void checkDevelMode() {
        File file = new File(MainApp.getDataPath() + "/usenewdata.txt");
        if (file.exists()) {
            Log.info("Using development mode for downloading data. So it means that test data will be downloaded instead of real one!!!!!!!!!!");
            this.devel = true;
        }
    }

    public static HistoryDataManager get() {
        if (instance == null) {
            instance = new HistoryDataManager();
        }
        return instance;
    }

    public synchronized boolean shouldInvalidateFutureDatas(String string, Date date) {
        this.ensureFuturesDao();
        Date date2 = this.futuresDao.getChangeDate(string);
        return this.shouldInvalidateDatas(date2, date);
    }

    private boolean shouldInvalidateDatas(Date date, Date date2) {
        if (date == null || date2 == null) {
            return false;
        }
        return date.after(date2) || date.equals(date2);
    }

    public boolean shouldSetFixedTimeForEod(TickerDto tickerDto, int n) {
        return n == 2 && tickerDto.isEod() && (tickerDto.getMarketName().equals("CME") || tickerDto.getMarketName().equals("CBOT"));
    }

    public boolean shouldShiftHoursForM1(TickerDto tickerDto) {
        return !tickerDto.isEod() && (tickerDto.getMarketName().equals("NYMEX") || tickerDto.getMarketName().equals("ICEUS") || tickerDto.getMarketName().equals("COMEX"));
    }

    public int getEodShiftDate(TickerDto tickerDto) {
        if (tickerDto.getMarketName().equals("CME")) {
            return 54900000;
        }
        if (tickerDto.getMarketName().equals("CBOT")) {
            return 50400000;
        }
        return 0;
    }

    public int getM1ShiftDate(TickerDto tickerDto) {
        if (tickerDto.getMarketName().equals("NYMEX") || tickerDto.getMarketName().equals("ICEUS") || tickerDto.getMarketName().equals("COMEX")) {
            return 3600000;
        }
        return 0;
    }

    public synchronized boolean shouldInvalidateStockDatas(String string, Date date) throws ClientProtocolException, IllegalStateException, NoSuchAlgorithmException, IOException, JDOMException, SQLException {
        this.ensureStockDao();
        Date date2 = this.stockDao.getChangeDate(string);
        return this.shouldInvalidateDatas(date2, date);
    }

    private boolean isDaoOld(long l) {
        long l2 = System.currentTimeMillis() - l;
        return l2 > 43200000L;
    }

    private synchronized void ensureFuturesDao() {
        if (this.futuresDao != null && !this.isDaoOld(this.futureDaoBorn)) {
            return;
        }
        this.disposeDao((AbstractHistoryDataDao)this.futuresDao);
        boolean bl = false;
        try {
            bl = this.ensureDataActual(false);
        }
        catch (Exception exception) {
            Log.error("Error while downloading new version", (Throwable)exception);
        }
        this.futuresDao = new FuturesHistoryDataDao(this.dataFolder);
        if (bl) {
            try {
                Log.debug("Creating indexes for futures");
                this.futuresDao.createIndexes();
                Log.debug("Indexes created");
            }
            catch (Exception exception) {
                Log.error("Error while generating indexes", (Throwable)exception);
            }
        }
        this.futureDaoBorn = System.currentTimeMillis();
    }

    private synchronized void ensureStockDao() {
        if (this.stockDao != null && !this.isDaoOld(this.stockDaoBorn)) {
            return;
        }
        this.disposeDao((AbstractHistoryDataDao)this.stockDao);
        boolean bl = false;
        try {
            bl = this.ensureDataActual(true);
        }
        catch (Exception exception) {
            Log.error("Error while downloading new version", (Throwable)exception);
        }
        this.stockDao = new StockHistoryDataDao(this.dataFolder);
        if (bl) {
            this.stockWasChanged = true;
            try {
                Log.debug("Creating indexes for equity");
                this.stockDao.createIndexes();
                Log.debug("Indexes created");
            }
            catch (Exception exception) {
                Log.error("Error while generating indexes", (Throwable)exception);
            }
        }
        this.stockDaoBorn = System.currentTimeMillis();
    }

    private int checkEvents() throws Exception {
        Map map = this.stockDao.getTickerRenamed();
        DataManager.get();
        ArrayList arrayList = DataManager.listSafe();
        int n = 0;
        for (DataInfo dataInfo : arrayList) {
            String string = dataInfo.uSymbol;
            if (dataInfo.source != 5 || string == null || dataInfo.dateTo == 0L) continue;
            if (dataInfo.symbol != null && dataInfo.symbol.endsWith("_limited.D")) {
                Log.debug("Skipping symbol {}", (Object)dataInfo.symbol);
                continue;
            }
            boolean bl = "D1".equals(dataInfo.timeframe);
            String string2 = bl && string.endsWith(".D") ? string.substring(0, string.length() - 2) : string;
            String string3 = this.getActualName(string2, dataInfo.dateTo, map, 10);
            String string4 = bl ? string3 + ".D" : string3;
            if (string.equalsIgnoreCase(string4)) continue;
            String string5 = dataInfo.symbol;
            String string6 = DataManager.renameUnderlayingData((String)"History", (String)dataInfo.symbol, (String)string4);
            Log.info("Renaming symbol {} -> {}", (Object)string5, (Object)string6);
            ++n;
        }
        return n;
    }

    private String getActualName(String string, long l, Map<String, List<TickerRenameInfo>> map, int n) {
        if (n == 0) {
            Log.info("Cycle in renaming found!");
            return string;
        }
        List<TickerRenameInfo> list = map.get(string);
        if (list != null) {
            TickerRenameInfo tickerRenameInfo = null;
            for (TickerRenameInfo tickerRenameInfo2 : list) {
                if (tickerRenameInfo2.getDate() <= l) continue;
                tickerRenameInfo = tickerRenameInfo2;
                break;
            }
            if (tickerRenameInfo != null) {
                return this.getActualName(tickerRenameInfo.getTickerTo(), tickerRenameInfo.getDate(), map, n - 1);
            }
        }
        return string;
    }

    public synchronized List<IdName> getStockMarkets() throws ClientProtocolException, IllegalStateException, IOException, JDOMException, SQLException, NoSuchAlgorithmException {
        this.ensureStockDao();
        return this.stockDao.getAllMarkets();
    }

    public synchronized List<TickerDto> getStockTickers(TickerFilterDto tickerFilterDto) throws ClientProtocolException, IllegalStateException, IOException, JDOMException, SQLException, NoSuchAlgorithmException {
        this.ensureStockDao();
        return this.stockDao.getTickers(tickerFilterDto);
    }

    public synchronized List<IdName> getFuturesMarkets() throws ClientProtocolException, IllegalStateException, IOException, JDOMException, SQLException, NoSuchAlgorithmException {
        this.ensureFuturesDao();
        return this.futuresDao.getAllMarkets();
    }

    public synchronized List<TickerDto> getFuturesTickers(TickerFilterDto tickerFilterDto) {
        this.ensureFuturesDao();
        try {
            return this.futuresDao.getTickers(tickerFilterDto);
        }
        catch (SQLException sQLException) {
            throw new RuntimeException(L.t((String)"Error while getting futures tickers", (Object[])new Object[0]), sQLException);
        }
    }

    public synchronized TickerDto getFutureTicker(String string) throws SQLException, ClientProtocolException, IllegalStateException, IOException, JDOMException, NoSuchAlgorithmException {
        this.ensureFuturesDao();
        return this.futuresDao.getTicker(string);
    }

    public synchronized TickerDto getFutureTicker(Long l) throws SQLException, ClientProtocolException, IllegalStateException, IOException, JDOMException, NoSuchAlgorithmException {
        this.ensureFuturesDao();
        return this.futuresDao.getTicker(l);
    }

    public synchronized TickerDto getStockTicker(String string) throws SQLException, ClientProtocolException, IllegalStateException, IOException, JDOMException, NoSuchAlgorithmException {
        this.ensureStockDao();
        return this.stockDao.getTicker(string);
    }

    public synchronized TickerDto getStockTicker(Long l) throws SQLException, ClientProtocolException, IllegalStateException, IOException, JDOMException, NoSuchAlgorithmException {
        this.ensureStockDao();
        return this.stockDao.getTicker(l);
    }

    private boolean ensureDataActual(boolean bl) throws ClientProtocolException, IllegalStateException, IOException, JDOMException, NoSuchAlgorithmException {
        Log.debug("Checking if history data database is actual");
        String string = this.downloadAvailableVersion(bl);
        String string2 = this.getCurrentDownloadedVersion(bl);
        if (string2 == null || !this.existsH2(bl)) {
            Log.debug("Missing version file or database - downloading entire database from server");
            this.downloadDatabase(bl);
            this.saveLatestVersion(bl, string);
            return true;
        }
        if (string2.compareTo(string) < 0) {
            Log.debug("Database is old. Downloaded version:" + string2 + ", available version: " + string);
            this.downloadDatabase(bl);
            this.saveLatestVersion(bl, string);
            return true;
        }
        return false;
    }

    private void saveLatestVersion(boolean bl, String string) throws IOException {
        Log.debug("Updating data version file");
        File file = null;
        file = this.devel ? new File(this.dataFolder, bl ? "data_stock_dev.version" : "data_futures_dev.version") : new File(this.dataFolder, bl ? "data_stock.version" : "data_futures.version");
        Files.write(file.toPath(), string.getBytes(), StandardOpenOption.CREATE);
    }

    private String getCurrentDownloadedVersion(boolean bl) throws IOException {
        File file = null;
        file = this.devel ? new File(this.dataFolder, bl ? "data_stock_dev.version" : "data_futures_dev.version") : new File(this.dataFolder, bl ? "data_stock.version" : "data_futures.version");
        if (!file.exists()) {
            return null;
        }
        return new String(Files.readAllBytes(file.toPath()));
    }

    private boolean existsH2(boolean bl) {
        File file = new File(this.dataFolder, bl ? "data_stock.h2.db" : "data_futures.h2.db");
        return file.exists();
    }

    private void downloadDatabase(boolean bl) throws ClientProtocolException, IllegalStateException, IOException, JDOMException, NoSuchAlgorithmException {
        DownloadMessageHandler downloadMessageHandler = new DownloadMessageHandler(){

            @Override
            public void onDownloadMessage(String string, String string2) {
                Log.error("Timeout while downloading database.");
            }
        };
        byte[] byArray = this.doDownload(this.getH2Url(bl), 0, downloadMessageHandler);
        if (byArray == null) {
            Log.error("Database download failed.");
            throw new RuntimeException(L.t((String)"Database download failed. No content.", (Object[])new Object[0]));
        }
        this.unzipH2(byArray);
        Log.debug("Database downloaded and unziped");
    }

    private String downloadAvailableVersion(boolean bl) throws ClientProtocolException, IllegalStateException, IOException, JDOMException, NoSuchAlgorithmException {
        DownloadMessageHandler downloadMessageHandler = new DownloadMessageHandler(){

            @Override
            public void onDownloadMessage(String string, String string2) {
                Log.error("Timeout while downloading version file.");
            }
        };
        String string = this.getVersionUrl(bl);
        byte[] byArray = this.doDownload(string, 0, downloadMessageHandler);
        if (byArray == null) {
            Log.error("Download database descriptions failed from server: " + string);
            throw new RuntimeException(L.t((String)"Database descriptions download failed. No content.", (Object[])new Object[0]));
        }
        return new String(byArray);
    }

    private boolean useHkServer() {
        String string = MainApp.settings().get("cdnPreferred", DataSources.DOWNLOAD_TYPE_CDN);
        return DataSources.DOWNLOAD_TYPE_CDN_CN.equals(string);
    }

    public String normalizeSymbol(String string) {
        if (string.equalsIgnoreCase("CON") || string.startsWith("CON.") || string.equalsIgnoreCase("PRN") || string.startsWith("PRN.") || string.equalsIgnoreCase("AUX") || string.startsWith("AUX.")) {
            string = "_" + string;
        }
        return string;
    }

    public byte[] downloadHistoryData(TickerDto tickerDto, TickerKind tickerKind, int n, int n2, String string, String string2, DownloadMessageHandler downloadMessageHandler) throws Exception {
        boolean bl = BMF_ID.equals(tickerDto.getMarketId());
        if (string2.equals("M1")) {
            string2 = "minutes";
            if (bl) {
                string = string.substring(0, string.length() - 3);
            }
        } else {
            string2 = "eod";
            string = bl ? string.substring(0, string.length() - 3) : string.substring(0, string.length() - 2);
        }
        String string3 = HistoryDataManager.getZipDataFilename(n);
        string = this.normalizeSymbol(string);
        String string4 = String.format("%s/%s/%s.zip", string2, string, string3);
        String string5 = this.getDataUrl();
        int n3 = string5.indexOf("/", 10);
        Log.info("Downloading {} from server: {}", (Object)string, (Object)string5.substring(0, n3));
        return this.doPostDownload(string5, string4, tickerKind.forDownload(), 30, downloadMessageHandler);
    }

    public String getAdjustedIdent(String string) {
        if (string.length() <= 3) {
            return String.valueOf(string.charAt(0));
        }
        String string2 = string.substring(0, 2);
        if (string2.endsWith(".")) {
            string2 = String.valueOf(string.charAt(0));
        }
        return string2;
    }

    public byte[] downloadAdjustedHistoryData(String string, DownloadMessageHandler downloadMessageHandler) throws Exception {
        String string2 = String.format("eod/adjusted_%s/data.zip", string);
        String string3 = this.getDataUrl();
        return this.doPostDownload(string3, string2, TickerKind.STOCK.forDownload(), 30, downloadMessageHandler);
    }

    /*
     * Loose catch block
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    private byte[] doDownload(String string, int n, DownloadMessageHandler downloadMessageHandler) throws ClientProtocolException, IOException {
        try (CloseableHttpClient closeableHttpClient = (CloseableHttpClient)HttpApacheManager.getInstance().getClient(40);){
            for (int i = 1; i <= 5; ++i) {
                byte[] byArray;
                CloseableHttpResponse closeableHttpResponse;
                try {
                    closeableHttpResponse = closeableHttpClient.execute((HttpUriRequest)new HttpGet(string));
                    int n2 = closeableHttpResponse.getStatusLine().getStatusCode();
                    if (n2 != 200) {
                        Log.error("Http result: " + n2 + " for url: " + string);
                        this.notifyError(downloadMessageHandler, "Error while downloding file. Http code: " + n2);
                        byte[] byArray2 = null;
                        return byArray2;
                    }
                }
                catch (SocketTimeoutException | SSLProtocolException | ConnectTimeoutException throwable) {
                    Log.error("Download timeout for url: " + string, throwable);
                    long l = 40000L;
                    Log.debug("Used timeout timeout: " + l + "ms ");
                    if (throwable instanceof ConnectTimeoutException) {
                        Log.debug("Host:" + ((ConnectTimeoutException)throwable).getHost());
                    }
                    this.notifyError(downloadMessageHandler, "Download timeout. Waiting for: 30sec");
                    try {
                        if (n == 0) continue;
                        Thread.sleep(n * 1000);
                        continue;
                    }
                    catch (InterruptedException interruptedException) {
                        byte[] byArray3 = null;
                        return byArray3;
                    }
                    catch (Exception exception) {
                        Log.error("Error while downloading url: " + string, (Throwable)exception);
                    }
                    continue;
                }
                InputStream inputStream = closeableHttpResponse.getEntity().getContent();
                byte[] byArray4 = byArray = IOUtils.toByteArray((InputStream)inputStream);
                return byArray4;
            }
            byte[] byArray = null;
            return byArray;
        }
    }

    private void notifyError(DownloadMessageHandler downloadMessageHandler, String string) {
        if (downloadMessageHandler != null) {
            downloadMessageHandler.onDownloadMessage(string, null);
        }
    }

    /*
     * WARNING - Removed back jump from a try to a catch block - possible behaviour change.
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    private byte[] doPostDownload(String string, String string2, String string3, int n, DownloadMessageHandler downloadMessageHandler) throws Exception {
        if (this.devel && string2.startsWith("eod")) {
            return this.doPostDownloadDevel(string2, downloadMessageHandler);
        }
        try (CloseableHttpClient closeableHttpClient = (CloseableHttpClient)HttpApacheManager.getInstance().getClient(40);){
            for (int i = 1; i <= 5; ++i) {
                InputStream inputStream;
                int n2;
                V571hfnsHw v571hfnsHw;
                try {
                    HttpPost httpPost = new HttpPost(string);
                    ArrayList<BasicNameValuePair> arrayList = new ArrayList<BasicNameValuePair>();
                    v571hfnsHw = MainApp.v571hfnsHw();
                    arrayList.add(new BasicNameValuePair("l", v571hfnsHw.eHvc2JguAd()));
                    arrayList.add(new BasicNameValuePair("hwid", v571hfnsHw.nmFllxIfvN()));
                    arrayList.add(new BasicNameValuePair("dsn", this.diskSn));
                    arrayList.add(new BasicNameValuePair("mac", this.macAddr));
                    arrayList.add(new BasicNameValuePair("path", string2));
                    arrayList.add(new BasicNameValuePair("type", string3));
                    httpPost.setEntity((HttpEntity)new UrlEncodedFormEntity(arrayList));
                    CloseableHttpResponse closeableHttpResponse = closeableHttpClient.execute((HttpUriRequest)httpPost);
                    n2 = closeableHttpResponse.getStatusLine().getStatusCode();
                    inputStream = closeableHttpResponse.getEntity().getContent();
                    if (n2 >= 200 && n2 < 300) {
                        byte[] byArray;
                        byte[] byArray2 = byArray = IOUtils.toByteArray((InputStream)inputStream);
                        return byArray2;
                    }
                }
                catch (SocketTimeoutException | SSLProtocolException | ConnectTimeoutException throwable) {
                    Log.error("Download timeout for " + string2, throwable);
                    this.notifyError(downloadMessageHandler, "Download timeout. Waiting for: 30sec");
                    try {
                        if (n == 0) continue;
                        Thread.sleep(n * 1000);
                        continue;
                    }
                    catch (InterruptedException interruptedException) {
                        v571hfnsHw = null;
                        if (closeableHttpClient == null) return v571hfnsHw;
                        closeableHttpClient.close();
                        return v571hfnsHw;
                    }
                }
                catch (Exception exception) {
                    Log.error("Error while downloading " + string2, (Throwable)exception);
                    throw exception;
                }
                {
                    byte[] byArray = IOUtils.toByteArray((InputStream)inputStream);
                    String string4 = new String(byArray);
                    String string5 = null;
                    Log.debug("Download request for h:{} failed", (Object)v571hfnsHw.nmFllxIfvN());
                    Log.error("Download failed with code: " + n2 + ". Response content: " + string4);
                    try {
                        JSONObject jSONObject = new JSONObject(string4);
                        string5 = jSONObject.getString("error");
                        throw new SQException("Error while downloading history data: " + string5);
                    }
                    catch (Exception exception) {
                        Log.error("Error while parsing history data response", (Throwable)exception);
                        throw new RuntimeException(L.t((String)"Error while parsing history data response.", (Object[])new Object[0]), exception);
                    }
                }
            }
            byte[] byArray = null;
            return byArray;
        }
    }

    private byte[] doPostDownloadDevel(String string, DownloadMessageHandler downloadMessageHandler) throws ClientProtocolException, IOException {
        String string2 = "https://cdn.strategyquantcdn.com/data/barchart_test/" + string;
        return this.doDownload(string2, 0, downloadMessageHandler);
    }

    public static String getZipDataFilename(long l) {
        if (l < 2019L) {
            return "data00";
        }
        return "data01";
    }

    private void unzipH2(byte[] byArray) throws IOException {
        block11: {
            byte[] byArray2 = new byte[1024];
            try (ZipInputStream zipInputStream = new ZipInputStream(new ByteArrayInputStream(byArray));){
                ZipEntry zipEntry = zipInputStream.getNextEntry();
                if (zipEntry == null) break block11;
                File file = new File(this.dataFolder, zipEntry.getName());
                try (BufferedOutputStream bufferedOutputStream = new BufferedOutputStream(new FileOutputStream(file));){
                    int n;
                    while ((n = zipInputStream.read(byArray2)) > 0) {
                        bufferedOutputStream.write(byArray2, 0, n);
                    }
                }
            }
        }
    }

    public synchronized CommodityDto getCommodity(Long l) throws SQLException, ClientProtocolException, IllegalStateException, NoSuchAlgorithmException, IOException, JDOMException {
        this.ensureFuturesDao();
        return this.futuresDao.getCommodity(l);
    }

    public synchronized CommodityDto getCommodityForFuture(String string) throws ClientProtocolException, IllegalStateException, NoSuchAlgorithmException, IOException, JDOMException, SQLException {
        this.ensureFuturesDao();
        return this.futuresDao.getCommodityForFuture(string);
    }

    public synchronized List<CommodityDto> getCommodities(String[] stringArray) throws SQLException {
        this.ensureFuturesDao();
        return this.futuresDao.getCommoditiesForFutures(stringArray);
    }

    private String getHtml(List<TickerDto> list) {
        HashMap hashMap = new HashMap();
        for (TickerDto object2 : list) {
            List list2 = (List)hashMap.get(object2.getMarketName());
            if (list2 == null) {
                list2 = new LinkedList();
                hashMap.put(object2.getMarketName(), list2);
            }
            list2.add(object2);
        }
        DateTimeFormatter dateTimeFormatter = DateTimeFormat.forPattern((String)"dd.MM.YYYY");
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append("<table>");
        for (String string : hashMap.keySet()) {
            stringBuilder.append("<tr><td class=\"dataType\" colspan=\"6\">" + this.safePrint(string) + "</td></tr>\n");
            stringBuilder.append(String.format("<tr class=\"dataHeader\"><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n", "Ticker", "Name", "Type", "Exchange", "Data From"));
            List list3 = (List)hashMap.get(string);
            for (TickerDto tickerDto : list3) {
                String string2 = tickerDto.getDateFrom() == null ? "" : dateTimeFormatter.print(tickerDto.getDateFrom().getTime());
                String string3 = tickerDto.getName();
                if (tickerDto.isEod()) {
                    string3 = string3 + " - Daily";
                }
                stringBuilder.append(String.format("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>", tickerDto.getTicker(), this.safePrint(string3), this.safePrint(tickerDto.getType()), this.safePrint(tickerDto.getMarketName()), string2));
            }
        }
        stringBuilder.append("</table>");
        return stringBuilder.toString();
    }

    public synchronized String generateStockHtml() throws ClientProtocolException, IllegalStateException, NoSuchAlgorithmException, IOException, JDOMException, SQLException {
        this.ensureStockDao();
        List list = this.stockDao.getTickers(new TickerFilterDto());
        return this.getHtml(list);
    }

    public synchronized String generateFuturesHtml() throws ClientProtocolException, IllegalStateException, NoSuchAlgorithmException, IOException, JDOMException, SQLException {
        this.ensureFuturesDao();
        List list = this.futuresDao.getTickers(new TickerFilterDto());
        return this.getHtml(list);
    }

    private Object safePrint(String string) {
        return string != null ? string : "-";
    }

    public synchronized void init() {
        try {
            this.ensureFuturesDao();
            this.ensureStockDao();
        }
        catch (Throwable throwable) {
            Log.error("Error while history data init", throwable);
        }
    }

    public synchronized void initAsync() {
        new Thread(new Runnable(){

            @Override
            public void run() {
                HistoryDataManager.get().init();
            }
        }).start();
    }

    private void disposeDao(AbstractHistoryDataDao abstractHistoryDataDao) {
        if (abstractHistoryDataDao != null) {
            abstractHistoryDataDao.dispose();
        }
    }

    public synchronized void dispose() {
        this.disposeDao((AbstractHistoryDataDao)this.futuresDao);
        this.disposeDao((AbstractHistoryDataDao)this.stockDao);
    }

    public String getStockExchange(String string) throws SQLException {
        this.ensureStockDao();
        return this.stockDao.getExchangeForTicker(string);
    }

    public String getFuturesExchange(String string) throws SQLException {
        this.ensureFuturesDao();
        return this.futuresDao.getExchangeForTicker(string);
    }

    public void checkRenamedHistoryTickers() throws Exception {
        this.ensureStockDao();
        Log.debug("Checking renamed of stocks starting...");
        long l = System.currentTimeMillis();
        if (this.stockWasChanged) {
            int n = this.checkEvents();
            Log.info("Total renamed tickers {}", (Object)n);
        }
        Log.debug("Checking renamed of stocks is over in {} ms", (Object)(System.currentTimeMillis() - l));
    }
}

