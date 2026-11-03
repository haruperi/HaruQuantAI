/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.DataCloner
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.utils.IProgressListener
 *  com.strategyquant.lib.utils.Pair
 *  org.apache.http.Header
 *  org.apache.http.HttpResponse
 *  org.apache.http.client.methods.HttpGet
 *  org.apache.http.client.methods.HttpUriRequest
 *  org.apache.http.impl.client.CloseableHttpClient
 *  org.apache.http.impl.client.HttpClientBuilder
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.yahoo;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataCloner;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.lib.utils.Pair;
import com.strategyquant.tradinglib.dukascopy.DukascopyBinaryMerger;
import com.strategyquant.tradinglib.dukascopy.DukascopyUtils;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import com.strategyquant.tradinglib.yahoo.YahooHelper;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import org.apache.http.Header;
import org.apache.http.HttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClientBuilder;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class YahooDownloader {
    public static final Logger Log = LoggerFactory.getLogger(YahooDownloader.class);
    private static final int HOUR_CONSTANT = 3600;
    protected boolean canceled = false;
    protected boolean stopping = false;
    protected boolean paused = false;
    protected DukascopyBinaryMerger dataMerger;
    private DataBinReaderNew reader;
    private DataBinWriterNew writer;
    private volatile int avgDownloadSpeedCounter = 0;
    private volatile double avgDownloadSpeed = 0.0;
    private long lastPerformed = 0L;
    protected String jobId;
    protected DataManagerProgressListener listener;
    protected DataInfo dataInfo;
    protected ImportInfo importInfo;
    SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
    private YahooHelper yahooHelper;

    public void performDownload(String string, DataManagerProgressListener dataManagerProgressListener, DataInfo dataInfo, ImportInfo importInfo) throws Exception {
        this.jobId = string;
        this.listener = dataManagerProgressListener;
        this.dataInfo = dataInfo;
        this.importInfo = importInfo;
        this.canceled = false;
        this.stopping = false;
        this.yahooHelper = new YahooHelper();
        Log.debug("Starting download job for symbol:" + importInfo.symbol);
        try {
            this.prepareFiles();
            this.dataMerger = new DukascopyBinaryMerger("Downloaded", string, 1, importInfo);
            this.dataMerger.setProgressListener(dataManagerProgressListener);
            this.dataMerger.setWriter(this.writer);
            this.dataMerger.setReader(this.reader);
            dataManagerProgressListener.setMessage(L.t((String)"Starting download...", (Object[])new Object[0]));
            Log.debug("Starting download");
            this.download();
            this.finish();
            this.closeFiles(true);
            this.recomputeClonedData();
        }
        catch (Exception exception) {
            Log.error("Error while performing Yahoo data download", (Throwable)exception);
            this.onError("Error while performing Yahoo data download. Detail: " + exception.getMessage(), importInfo);
            throw new Exception(L.t((String)"Error while performing %s data download.\n%s", (Object[])new Object[]{dataInfo.symbol, exception.getMessage()}));
        }
        finally {
            DataManagerDataProgress.get().removeListener(importInfo.symbol);
            Log.debug("Download job for symbol:" + importInfo.symbol + " finished");
        }
    }

    private void download() throws Exception {
        long l = this.importInfo.dateFrom;
        long l2 = this.importInfo.dateTo;
        if (l == 0L) {
            l = -9999999999999L;
        }
        if ((l = this.dataMerger.checkDate(l)) > l2) {
            return;
        }
        long l3 = this.dataMerger.getPerformedDays();
        long l4 = System.currentTimeMillis();
        this.dataMerger.register(0, l / 1000L);
        this.dataMerger.reset(1);
        String string = null;
        String string2 = null;
        for (int i = 0; i < 3; ++i) {
            try {
                string2 = "https://query1.finance.yahoo.com/v8/finance/chart/" + URLEncoder.encode(this.dataInfo.uSymbol, "UTF-8") + "?period1=" + l / 1000L + "&period2=" + l2 / 1000L + "&interval=1d&events=history";
                string = this.getUrlContent(string2, true, null);
                if (string.contains("Invalid cookie")) {
                    Log.error("Cannot download data from yahoo. Invalid cookie. " + string2);
                    throw new Exception(L.t((String)"Cannot download data from Yahoo.", (Object[])new Object[0]));
                }
                break;
            }
            catch (Exception exception) {
                Log.error("Failed to download data. Trying again ...", (Throwable)exception);
                Thread.sleep(1000L);
                continue;
            }
        }
        if (string == null) {
            throw new Exception(L.t((String)"Cannot download data from Yahoo.", (Object[])new Object[0]));
        }
        JSONObject jSONObject = new JSONObject(string);
        JSONObject jSONObject2 = jSONObject.getJSONObject("chart");
        if (!jSONObject2.isNull("error")) {
            Object object = jSONObject2.get("error");
            throw new Exception(L.t((String)("Error while downloading data from Yahoo. " + object.toString()), (Object[])new Object[0]));
        }
        JSONArray jSONArray = jSONObject2.getJSONArray("result");
        JSONObject jSONObject3 = jSONArray.getJSONObject(0);
        JSONArray jSONArray2 = jSONObject3.getJSONArray("timestamp");
        JSONObject jSONObject4 = jSONObject3.getJSONObject("indicators");
        JSONObject jSONObject5 = jSONObject4.getJSONArray("quote").getJSONObject(0);
        JSONArray jSONArray3 = jSONObject5.getJSONArray("open");
        JSONArray jSONArray4 = jSONObject5.getJSONArray("high");
        JSONArray jSONArray5 = jSONObject5.getJSONArray("low");
        JSONArray jSONArray6 = jSONObject5.getJSONArray("close");
        JSONArray jSONArray7 = jSONObject5.getJSONArray("volume");
        VersatileData versatileData = null;
        for (int i = 0; i < jSONArray2.length(); ++i) {
            versatileData = this.parseData(jSONArray2, jSONArray3, jSONArray4, jSONArray5, jSONArray6, jSONArray7, i);
            if (versatileData == null) continue;
            this.dataMerger.updateSaveProgress(versatileData.time);
            this.dataMerger.storeToQueue(0, versatileData);
        }
        this.dataMerger.tryToSaveQueue(l);
        this.evaluateSpeed(l4, l3);
        if (this.dataMerger.getReader() != null) {
            this.dataMerger.readTill(SQTime.addDays((long)versatileData.time, (int)1), false);
        }
    }

    private VersatileData parseData(JSONArray jSONArray, JSONArray jSONArray2, JSONArray jSONArray3, JSONArray jSONArray4, JSONArray jSONArray5, JSONArray jSONArray6, int n) {
        try {
            VersatileData versatileData = new VersatileData();
            versatileData.time = jSONArray.getLong(n) * 1000L;
            versatileData.open = jSONArray2.getDouble(n);
            versatileData.high = jSONArray3.getDouble(n);
            versatileData.low = jSONArray4.getDouble(n);
            versatileData.close = jSONArray5.getDouble(n);
            versatileData.volume = jSONArray2.getInt(n);
            return versatileData;
        }
        catch (Exception exception) {
            Log.warn("Skipping yahoo record, due invalid content");
            return null;
        }
    }

    private VersatileData parseData(String[] stringArray) throws Exception {
        VersatileData versatileData = new VersatileData();
        versatileData.time = this.sdf.parse(stringArray[0]).getTime();
        versatileData.open = Double.parseDouble(stringArray[1]);
        versatileData.high = Double.parseDouble(stringArray[2]);
        versatileData.low = Double.parseDouble(stringArray[3]);
        versatileData.close = Double.parseDouble(stringArray[4]);
        versatileData.volume = Double.parseDouble(stringArray[6]);
        return versatileData;
    }

    private String[] getCookieCrumb() throws Exception {
        String string = null;
        String string2 = null;
        try {
            CloseableHttpClient closeableHttpClient = HttpClientBuilder.create().build();
            HttpGet httpGet = new HttpGet("https://finance.yahoo.com/quote/SPY");
            HttpResponse httpResponse = closeableHttpClient.execute((HttpUriRequest)httpGet);
            if (httpResponse.getStatusLine().getStatusCode() != 200) {
                throw new Exception(L.t((String)"HTML status code - %d", (Object[])new Object[]{httpResponse.getStatusLine().getStatusCode()}));
            }
            for (Header header : httpResponse.getAllHeaders()) {
                if (!header.getName().equalsIgnoreCase("Set-Cookie")) continue;
                string2 = header.getValue();
            }
            InputStream inputStream = httpResponse.getEntity().getContent();
            InputStreamReader inputStreamReader = new InputStreamReader(inputStream, StandardCharsets.UTF_8);
            BufferedReader bufferedReader = new BufferedReader(inputStreamReader);
            String string3 = "CrumbStore\":{\"crumb\":\"";
            String string4 = null;
            while ((string4 = bufferedReader.readLine()) != null) {
                if (!string4.contains(string3)) continue;
                int n = string4.indexOf("CrumbStore\":{\"crumb\":\"") + string3.length();
                string = string4.substring(n, string4.indexOf("\"", n));
                break;
            }
            bufferedReader.close();
        }
        catch (Error error) {
            throw new Exception(L.t((String)"Cannot get Yahoo cookie crumb.", (Object[])new Object[0]), error);
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Cannot get Yahoo cookie crumb.", (Object[])new Object[0]), exception);
        }
        if (string == null || string2 == null) {
            throw new Exception(L.t((String)"Cannot get Yahoo cookies / crumb.", (Object[])new Object[0]));
        }
        return new String[]{string, string2};
    }

    private String getUrlContent(String string, boolean bl, String string2) throws Exception {
        CloseableHttpClient closeableHttpClient = HttpClientBuilder.create().build();
        HttpGet httpGet = new HttpGet(string);
        HttpResponse httpResponse = null;
        try {
            httpResponse = closeableHttpClient.execute((HttpUriRequest)httpGet);
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Unable to get data from the URL '%s'", (Object[])new Object[]{string}), exception);
        }
        String string3 = SQUtils.inputStreamToString((InputStream)httpResponse.getEntity().getContent());
        int n = httpResponse.getStatusLine().getStatusCode();
        if (bl && n >= 400) {
            throw new Exception(L.t((String)"HTML status code - %d. Reason: %s", (Object[])new Object[]{httpResponse.getStatusLine().getStatusCode(), string3}));
        }
        return string3;
    }

    protected void prepareFiles() throws Exception {
        Log.debug("Preparing data files");
        this.listener.setMessage(L.t((String)"Preparing data files", (Object[])new Object[0]));
        Pair<DataBinReaderNew, DataBinWriterNew> pair = DukascopyUtils.prepareFiles(this.importInfo, this.dataInfo.timeframe);
        this.reader = (DataBinReaderNew)pair.getA();
        this.writer = (DataBinWriterNew)pair.getB();
    }

    protected void closeFiles(boolean bl) {
        try {
            this.writer.close();
        }
        catch (Exception exception) {
            // empty catch block
        }
        try {
            if (this.reader != null) {
                this.reader.closeFile();
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
        if (bl) {
            DukascopyUtils.deleteCopyFile(this.importInfo.symbol, "D1");
        } else {
            DukascopyUtils.revertCopyFile(this.importInfo.symbol, "D1");
        }
    }

    protected void finish() {
        try {
            if (this.canceled) {
                this.dataMerger.setStopped(this.canceled);
            }
            this.dataMerger.finish();
            long l = this.dataMerger.getFromDate();
            long l2 = this.dataMerger.getToDate();
            if (l != -1L && l2 != -1L) {
                DataManager.updateData((String)this.dataInfo.connection, (String)this.dataInfo.symbol, (long)l, (long)l2, (int)this.dataMerger.getSavedRows(), (long)0L, (int)this.dataInfo.barTimeType, (String)this.dataInfo.timeframe, (String)"Etc/UCT");
            }
        }
        catch (Exception exception) {
            Log.error("Error while saving results", (Throwable)exception);
            throw new RuntimeException(L.t((String)"Error while saving results", (Object[])new Object[0]));
        }
    }

    protected void recomputeClonedData() {
        try {
            DataCloner dataCloner = new DataCloner();
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)this.importInfo.symbol);
            ArrayList arrayList = DataManager.listCloned((int)dataInfo.id);
            for (int i = 0; i < arrayList.size(); ++i) {
                DataInfo dataInfo2 = (DataInfo)arrayList.get(i);
                DataManager.clearData((String)dataInfo2.connection, (String)dataInfo2.symbol);
                this.listener.setMessage(L.t((String)"Recomputing cloned data", (Object[])new Object[0]));
                String[] stringArray = dataInfo2.timezone.split("\\|");
                String string = stringArray[0];
                int n = 0;
                try {
                    n = Integer.parseInt(stringArray[1]);
                }
                catch (Exception exception) {
                    // empty catch block
                }
                dataCloner.cloneToTimezone(this.importInfo.symbol, dataInfo2.symbol, string, n, dataInfo2.removeWeekends, null, (IProgressListener)this.listener);
            }
        }
        catch (Exception exception) {
            Log.error("Error while recomputing cloned data.", (Throwable)exception);
            throw new RuntimeException(L.t((String)"Error while recomputing cloned data.", (Object[])new Object[0]));
        }
    }

    protected void onError(String string, ImportInfo importInfo) {
        if (this.dataMerger != null) {
            this.dataMerger.skipAllProgress();
        }
        this.listener.onError(string);
        this.closeFiles(false);
    }

    protected void evaluateSpeed(long l, long l2) {
        long l3 = this.dataMerger.getPerformedDays();
        long l4 = System.currentTimeMillis();
        if (l3 != l2) {
            this.lastPerformed = l3 - l2;
        }
        double d = (double)(l4 - l) / 1000.0;
        double d2 = (double)this.lastPerformed / d;
        double d3 = (double)Math.round(d2 * 10.0) / 10.0;
        double d4 = this.avgDownloadSpeed / (double)this.avgDownloadSpeedCounter;
        String string = "Kbps";
        if (d4 > 1024.0) {
            string = "Mbps";
            d4 /= 1024.0;
        }
        double d5 = (double)Math.round(d4 * 10.0) / 10.0;
        String string2 = " (" + d3 + " days/sec) - " + d5 + string;
        this.listener.setSpeed(string2);
        this.avgDownloadSpeedCounter = 0;
        this.avgDownloadSpeed = 0.0;
        long l5 = this.dataMerger.getRestDays();
        if (l5 > 0L) {
            long l6 = (long)((double)l5 * d);
            this.listener.setEstimation(this.evaluateTime(l6));
        }
    }

    private String evaluateTime(long l) {
        long l2 = l / 60L;
        long l3 = l / 3600L;
        StringBuilder stringBuilder = new StringBuilder();
        if (l3 > 0L) {
            stringBuilder.append(l3 + "hours ");
            long l4 = l2 - l3 * 60L;
            stringBuilder.append(l4 + "mins");
        } else if (l2 > 0L) {
            stringBuilder.append(l2 + "mins ");
            long l5 = l - l2 * 60L;
            stringBuilder.append(l5 + "secs");
        } else {
            stringBuilder.append(l + "secs");
        }
        return stringBuilder.toString();
    }

    protected void checkPaused() throws InterruptedException {
        if (!this.paused) {
            return;
        }
        this.listener.onPause();
        while (this.paused && !this.canceled) {
            Thread.sleep(100L);
        }
        this.listener.onContinue();
    }

    public void cancel() {
        this.canceled = true;
    }

    public void pause() {
        this.paused = true;
    }

    public void restart() {
        this.paused = false;
    }

    public boolean isCanceled() {
        return this.canceled;
    }
}

