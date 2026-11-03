/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.broker.BrokerDto
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.data.DataCloner
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.DukasDataManager
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.gridlib.compute.common.ExecuteOptions
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.utils.IProgressListener
 *  com.strategyquant.lib.utils.Pair
 *  com.strategyquant.qdm.QDM
 *  org.apache.commons.io.IOUtils
 *  org.apache.http.HttpEntity
 *  org.apache.http.HttpResponse
 *  org.apache.http.client.HttpClient
 *  org.apache.http.client.methods.HttpGet
 *  org.apache.http.client.methods.HttpUriRequest
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.dukascopy.job;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.data.DataCloner;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.DukasDataManager;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.gridlib.compute.common.ExecuteOptions;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.lib.utils.Pair;
import com.strategyquant.qdm.QDM;
import com.strategyquant.tradinglib.data.download.SpeedEvaluator;
import com.strategyquant.tradinglib.dukascopy.CdnCache;
import com.strategyquant.tradinglib.dukascopy.CdnDownloadJob;
import com.strategyquant.tradinglib.dukascopy.DownloadResultDto;
import com.strategyquant.tradinglib.dukascopy.DukascopyBinaryMerger;
import com.strategyquant.tradinglib.dukascopy.DukascopyUtils;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.dukascopy.job.DownloadRateCorrector;
import com.strategyquant.tradinglib.dukascopy.job.DownloadWithFlexibileSpeedJob;
import com.strategyquant.tradinglib.historyData.DownloadMessageHandler;
import com.strategyquant.tradinglib.historyData.HttpApacheManager;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import java.io.FilterInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.Serializable;
import java.security.KeyManagementException;
import java.security.KeyStoreException;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.concurrent.CancellationException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicInteger;
import org.apache.commons.io.IOUtils;
import org.apache.http.HttpEntity;
import org.apache.http.HttpResponse;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpUriRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DownloadDukascopySymbolJob
extends GridJob<Void> {
    private static final int START_HOUR_SUNDAY_FOREX = 19;
    private static final int MAX_M1_DOWNLOAD_PARALLEL = 3;
    private static final int HOUR_CONSTANT = 3600;
    private static final int TIMEOUT = 100;
    public static final String DOWNLOAD_GROUP = "DukascopyDownloadPerformerGroup";
    private static final int HOURS = 24;
    private static final long serialVersionUID = 1L;
    public static final Logger Log = LoggerFactory.getLogger(DownloadDukascopySymbolJob.class);
    private ImportInfo importInfo;
    private DukascopyBinaryMerger dukascopyMerger;
    private DataBinReaderNew reader;
    private DataBinWriterNew writer;
    private List<String> errors = new LinkedList<String>();
    private long currentDateTime = -1L;
    private DataManagerProgressListener progressListener;
    private volatile boolean stopped;
    private volatile boolean cdnError;
    private long endDateTime;
    private volatile boolean paused;
    private volatile AtomicInteger downloadCount = new AtomicInteger();
    private DownloadRateCorrector downloadCorrector = new DownloadRateCorrector();
    private SpeedEvaluator speedEvaluator = new SpeedEvaluator();
    private CdnCache cdnCache;
    private ExecuteOptions executeOptions;
    private volatile long downloadStarted = -1L;
    private LinkedList<GridJob<?>> currentDownloadJobs;
    private DownloadMessageHandler failedHandler;
    private String targetTimezone = "Etc/UCT";
    private DataInfo dataInfo;
    private Future<?> preloadFuture;
    private String baseCdnUrl;

    public DownloadDukascopySymbolJob(String string, String string2, ImportInfo importInfo) throws Exception {
        super(string2, 0, null);
        this.baseCdnUrl = string;
        this.importInfo = importInfo;
        this.executeOptions = new ExecuteOptions();
        this.executeOptions.setMaxRunningCount(6);
        this.currentDateTime = SQTime.correctDayStart((long)importInfo.dateFrom);
        this.endDateTime = SQTime.correctDayStart((long)importInfo.dateTo);
        long l = SQTime.correctDayStart((long)System.currentTimeMillis());
        if (this.endDateTime >= l) {
            this.endDateTime = SQTime.addDays((long)this.endDateTime, (int)-1);
        }
        this.failedHandler = new DownloadMessageHandler(){

            @Override
            public void onDownloadMessage(String string, String string2) {
                DownloadDukascopySymbolJob.this.progressListener.setMessage(string);
                if (string2 != null) {
                    DownloadDukascopySymbolJob.this.progressListener.setSpeed(string2);
                }
            }
        };
        this.dataInfo = DataManager.getDataInfo((String)"History", (String)importInfo.symbol);
        if (MainApp.v571hfnsHw().a1wUchdumV() && !MainApp.v571hfnsHw().xpoHYYsX() && !DukasDataManager.get().canFreeDownloadFromCdn(this.dataInfo)) {
            importInfo.useCDN = false;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private boolean loadCheckSumsForCDN() throws KeyManagementException, NoSuchAlgorithmException, KeyStoreException {
        if (!this.importInfo.useCDN) {
            return false;
        }
        this.progressListener.setMessage(L.t((String)"Loading symbol's checksums", (Object[])new Object[0]));
        int n = this.baseCdnUrl.indexOf("/", 10);
        Log.info("Downloading {} from server: {}", (Object)this.importInfo.symbol, (Object)this.baseCdnUrl.substring(0, n));
        String string = this.baseCdnUrl + "/" + this.importInfo.origSymbol + "/metadata.dat";
        HttpClient httpClient = HttpApacheManager.getInstance().getClient(100);
        HttpGet httpGet = new HttpGet(string);
        HashSet<String> hashSet = new HashSet<String>();
        FilterInputStream filterInputStream = null;
        try {
            HttpResponse httpResponse = httpClient.execute((HttpUriRequest)httpGet);
            int bl = httpResponse.getStatusLine().getStatusCode();
            if (bl < 200 || bl >= 300) {
                Log.error("Error while loading CDN database from url: {}. Got error code: {}", (Object)string, (Object)bl);
                boolean httpEntity = false;
                return httpEntity;
            }
            httpResponse.getEntity().getContent();
            HttpEntity iOException = httpResponse.getEntity();
            InputStream inputStream = iOException.getContent();
            byte[] byArray = IOUtils.toByteArray((InputStream)inputStream);
            String string2 = new String(byArray, "UTF-8");
            String[] stringArray = string2.split(";");
            if (stringArray != null) {
                for (String string3 : stringArray) {
                    if ((string3 = string3.trim()).isEmpty()) continue;
                    hashSet.add(string3);
                }
            }
        }
        catch (Exception exception) {
            Log.error("Error while loading CDN database from url:" + string, (Throwable)exception);
            boolean bl = false;
            return bl;
        }
        finally {
            httpGet.releaseConnection();
            if (filterInputStream != null) {
                try {
                    filterInputStream.close();
                }
                catch (IOException iOException) {}
            }
        }
        this.cdnCache = new CdnCache(this.getJobId(), this.baseCdnUrl, this.importInfo.origSymbol, hashSet, this.currentDateTime);
        return !hashSet.isEmpty();
    }

    private void checkPaused() throws InterruptedException {
        if (!this.paused) {
            return;
        }
        this.progressListener.onPause();
        while (this.paused && !this.stopped) {
            Thread.sleep(100L);
        }
        this.progressListener.onContinue();
    }

    private void prepareFiles() throws Exception {
        Log.debug("Preparing data files");
        this.progressListener.setMessage(L.t((String)"Preparing data files", (Object[])new Object[0]));
        String string = this.importInfo.downloadM1Data ? "M1" : "TICK";
        Pair<DataBinReaderNew, DataBinWriterNew> pair = DukascopyUtils.prepareFiles(this.importInfo, string);
        this.reader = (DataBinReaderNew)pair.getA();
        this.writer = (DataBinWriterNew)pair.getB();
    }

    public void setProgressListener(DataManagerProgressListener dataManagerProgressListener) {
        this.progressListener = dataManagerProgressListener;
    }

    private List<GridJob<DownloadResultDto>> generateDownloadJobs() throws Exception {
        LinkedList<GridJob<DownloadResultDto>> linkedList = new LinkedList<GridJob<DownloadResultDto>>();
        if (this.currentDateTime > this.endDateTime) {
            return linkedList;
        }
        this.currentDateTime = this.dukascopyMerger.checkDate(this.currentDateTime);
        if (this.currentDateTime > this.endDateTime) {
            return linkedList;
        }
        if (this.importInfo.useCDN) {
            int n;
            int n2;
            int n3 = n2 = this.importInfo.downloadM1Data ? 3 : 1;
            for (n = 0; this.currentDateTime <= this.endDateTime && n < n2; ++n) {
                String string = this.getJobId() + "_" + n + "_cdn";
                int n4 = SQTime.getFullYear((long)this.currentDateTime);
                int n5 = SQTime.getMonth((long)this.currentDateTime) + 1;
                int n6 = SQTime.getDay((long)this.currentDateTime);
                linkedList.add(new CdnDownloadJob(string, this.cdnCache, n4, n5, n6, 0, this.failedHandler));
                this.dukascopyMerger.register(n, this.currentDateTime);
                this.currentDateTime = SQTime.addDays((long)this.currentDateTime, (int)1);
            }
            this.dukascopyMerger.reset(n);
            return linkedList;
        }
        if (this.importInfo.downloadM1Data) {
            int n;
            for (n = 0; this.currentDateTime <= this.endDateTime && n < 3; ++n) {
                String string = DukascopyUtils.generateM1DukascopyUrl(this.currentDateTime, this.importInfo.origSymbol);
                String string2 = this.getJobId() + "_" + n;
                linkedList.add(this.createDukascopyDownloadJob(string, string2));
                this.dukascopyMerger.register(n, this.currentDateTime);
                this.currentDateTime = SQTime.addDays((long)this.currentDateTime, (int)1);
            }
            this.dukascopyMerger.reset(n);
            return linkedList;
        }
        int n = 0;
        if (this.importInfo.ignoreWeekend && SQTime.getDayOfWeek((long)this.currentDateTime) == 7) {
            n = 19;
            this.currentDateTime = SQTime.setHour((long)this.currentDateTime, (int)n);
        }
        for (int i = n; i < 24; ++i) {
            String string = DukascopyUtils.generateTickDukascopyUrl(this.currentDateTime, this.importInfo.origSymbol);
            String string3 = this.getJobId() + "_" + i;
            this.dukascopyMerger.register(i, this.currentDateTime);
            linkedList.add(this.createDukascopyDownloadJob(string, string3));
            this.currentDateTime = SQTime.addHours((long)this.currentDateTime, (int)1);
        }
        this.dukascopyMerger.resetWithBatchAndStart(n - 1, 24);
        return linkedList;
    }

    private GridJob<DownloadResultDto> createDukascopyDownloadJob(String string, String string2) {
        HashMap<String, Serializable> hashMap = new HashMap<String, Serializable>();
        hashMap.put("url", (Serializable)((Object)string));
        return new DownloadWithFlexibileSpeedJob(string2, 0, hashMap, this.downloadCorrector);
    }

    private List<GridJob<DownloadResultDto>> generateDownloadJobs(List<String> list) {
        LinkedList<GridJob<DownloadResultDto>> linkedList = new LinkedList<GridJob<DownloadResultDto>>();
        for (String string : list) {
            long l = this.dukascopyMerger.getDateForJob(string);
            String string2 = this.importInfo.downloadM1Data ? DukascopyUtils.generateM1DukascopyUrl(l, this.importInfo.origSymbol) : DukascopyUtils.generateTickDukascopyUrl(l, this.importInfo.origSymbol);
            linkedList.add(this.createDukascopyDownloadJob(string2, string));
        }
        return linkedList;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void messageReceived(GridMessage gridMessage) {
        super.messageReceived(gridMessage);
        switch (gridMessage.getMessageID()) {
            case 4: {
                this.stopped = true;
                this.progressListener.setMessage(L.t((String)"Stopping download - please wait", (Object[])new Object[0]));
                this.downloadCorrector.stop();
                if (this.cdnCache != null) {
                    this.cdnCache.stop();
                }
                if (this.preloadFuture != null) {
                    this.preloadFuture.cancel(true);
                }
                DownloadDukascopySymbolJob downloadDukascopySymbolJob = this;
                synchronized (downloadDukascopySymbolJob) {
                    if (this.currentDownloadJobs != null) {
                        for (GridJob gridJob : this.currentDownloadJobs) {
                            gridJob.messageReceived(gridMessage);
                        }
                    }
                    break;
                }
            }
            case 2: {
                this.paused = true;
                break;
            }
            case 3: {
                this.paused = false;
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public Void call() throws Exception {
        if (this.currentDateTime >= this.endDateTime) {
            this.progressListener.onProgress(100.0);
            this.progressListener.setMessage(L.t((String)"Completed", (Object[])new Object[0]));
            return null;
        }
        try {
            this.progressListener.onProgress(0.1);
            this.progressListener.setMessage(L.t((String)"Waiting in queue", (Object[])new Object[0]));
            Log.debug("Starting download job for symbol: {}", (Object)this.importInfo.symbol);
            int n = this.importInfo.downloadM1Data ? 3 : 24;
            this.dukascopyMerger = new DukascopyBinaryMerger("Writing ", this.getJobId(), n, this.importInfo);
            this.dukascopyMerger.setProgressListener(this.progressListener);
            this.dukascopyMerger.setIgnoreWeekend(this.importInfo.ignoreWeekend);
            this.handleBroker();
            if (this.stopped) {
                this.dukascopyMerger.setFinishProgress(L.t((String)"Stopped", (Object[])new Object[0]));
                this.sendRefreshMessage();
                Void void_ = null;
                return void_;
            }
            boolean bl = this.loadCheckSumsForCDN();
            if (!bl) {
                this.importInfo.useCDN = false;
            }
            this.progressListener.setDownloadType(bl ? L.t((String)"Fast download", (Object[])new Object[0]) : L.t((String)"Normal download", (Object[])new Object[0]));
            this.progressListener.setDataType(this.importInfo.downloadM1Data ? L.t((String)"M1 data", (Object[])new Object[0]) : L.t((String)"Tick data", (Object[])new Object[0]));
            this.prepareFiles();
            this.dukascopyMerger.setWriter(this.writer);
            this.dukascopyMerger.setReader(this.reader);
            this.progressListener.setMessage(L.t((String)"Downloading...", (Object[])new Object[0]));
            Log.debug("Starting download");
            if (this.cdnCache != null) {
                ExecutorService executorService = Executors.newSingleThreadExecutor();
                try {
                    this.preloadFuture = executorService.submit(() -> this.cdnCache.preload(this.currentDateTime, this.endDateTime, this.failedHandler));
                    this.preloadFuture.get();
                }
                catch (CancellationException cancellationException) {
                    // empty catch block
                }
                this.preloadFuture = null;
            }
            this.downloadStarted = System.currentTimeMillis();
            while (!this.stopped && !this.cdnError) {
                long l = this.dukascopyMerger.getPerformedDays();
                long l2 = System.currentTimeMillis();
                List<GridJob<DownloadResultDto>> list = this.generateDownloadJobs();
                Log.debug("Generating downloads jobs: {}", (Object)list.size());
                if (list.isEmpty()) break;
                if (this.downloadStarted == -1L) {
                    this.downloadStarted = System.currentTimeMillis();
                }
                DownloadDukascopySymbolJob downloadDukascopySymbolJob = this;
                synchronized (downloadDukascopySymbolJob) {
                    this.currentDownloadJobs = new LinkedList<GridJob<DownloadResultDto>>(list);
                }
                this.executeJobsAndWait(list);
                if (this.stopped) break;
                Log.debug("Download finished. Errors: {}", (Object)this.errors.size());
                this.downloadMissing();
                this.checkPaused();
                this.errors.clear();
                this.evaluateSpeed(l2, l);
                if (this.importInfo.downloadM1Data && this.reader != null) {
                    this.dukascopyMerger.readTill(this.currentDateTime, false);
                }
                if (!this.dukascopyMerger.isSaveError()) continue;
                this.onError(L.t((String)"Error while saving data", (Object[])new Object[0]));
                break;
            }
            this.finish();
            this.closeFiles(true);
            this.recomputeClonedData();
            if (this.cdnError) {
                this.onError(L.t((String)"Download problem - check your internet connection", (Object[])new Object[0]));
            } else {
                long l = (System.currentTimeMillis() - this.downloadStarted) / 1000L;
                String string = this.stopped ? L.t((String)"Stopped", (Object[])new Object[0]) : L.t((String)"Completed", (Object[])new Object[0]);
                this.dukascopyMerger.setFinishProgress(string + " in " + this.evaluateTime(l));
            }
            this.sendRefreshMessage();
        }
        catch (Exception exception) {
            Log.error("Error while performing dukascopy import", (Throwable)exception);
            this.onError(L.t((String)"Error while performing dukascopy import", (Object[])new Object[0]));
        }
        finally {
            if (this.cdnCache != null) {
                this.cdnCache.clean();
            }
            DataManagerDataProgress.get().removeListener(this.importInfo.symbol);
            Log.debug("Download job for symbol: {} finished", (Object)this.importInfo.symbol);
        }
        return null;
    }

    private void handleBroker() {
        if (this.dataInfo.brokerId != -1) {
            String string;
            BrokerDto brokerDto = BrokerManager.getInstance().getBroker(Integer.valueOf(this.dataInfo.brokerId));
            this.targetTimezone = string = brokerDto.getMtTimezone();
            this.dukascopyMerger.setTargetTimezone(this.targetTimezone);
        }
    }

    private void evaluateSpeed(long l, long l2) {
        long l3 = this.dukascopyMerger.getPerformedDays();
        long l4 = System.currentTimeMillis();
        double d = (double)(l4 - this.downloadStarted) / 1000.0;
        double d2 = (double)l3 / d;
        double d3 = (double)Math.round(d2 * 10.0) / 10.0;
        String string = " (" + d3 + " " + L.t((String)"days/sec", (Object[])new Object[0]) + ") - " + this.speedEvaluator.getSpeed();
        this.progressListener.setSpeed(string);
        this.speedEvaluator.reset();
        long l5 = this.dukascopyMerger.getRestDays();
        if (l5 > 0L) {
            double d4 = d / (double)l3;
            long l6 = (long)((double)l5 * d4);
            this.progressListener.setEstimation(this.evaluateTime(l6));
        }
    }

    private String evaluateTime(long l) {
        long l2 = l / 60L;
        long l3 = l / 3600L;
        StringBuilder stringBuilder = new StringBuilder();
        if (l3 > 0L) {
            stringBuilder.append(l3 + L.t((String)"hours", (Object[])new Object[0]) + " ");
            long l4 = l2 - l3 * 60L;
            stringBuilder.append(l4 + L.t((String)"mins", (Object[])new Object[0]));
        } else if (l2 > 0L) {
            stringBuilder.append(l2 + L.t((String)"mins", (Object[])new Object[0]) + " ");
            long l5 = l - l2 * 60L;
            stringBuilder.append(l5 + L.t((String)"secs", (Object[])new Object[0]));
        } else {
            stringBuilder.append(l + L.t((String)"secs", (Object[])new Object[0]));
        }
        return stringBuilder.toString();
    }

    private void recomputeClonedData() {
        try {
            DataCloner dataCloner = new DataCloner();
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)this.importInfo.symbol);
            ArrayList arrayList = DataManager.listCloned((int)dataInfo.id);
            for (int i = 0; i < arrayList.size(); ++i) {
                DataInfo dataInfo2 = (DataInfo)arrayList.get(i);
                DataManager.clearData((String)dataInfo2.connection, (String)dataInfo2.symbol);
                this.progressListener.setMessage(L.t((String)"Recomputing cloned data", (Object[])new Object[0]));
                String[] stringArray = dataInfo2.timezone.split("\\|");
                String string = stringArray[0];
                int n = 0;
                try {
                    n = Integer.parseInt(stringArray[1]);
                }
                catch (Exception exception) {
                    // empty catch block
                }
                dataCloner.cloneToTimezone(this.importInfo.symbol, dataInfo2.symbol, string, n, dataInfo2.removeWeekends, null, (IProgressListener)this.progressListener);
            }
        }
        catch (Exception exception) {
            Log.error("Error while recomputing cloned data.", (Throwable)exception);
            this.onError(L.t((String)"Error while recomputing cloned data.", (Object[])new Object[0]));
        }
    }

    private void onError(String string) {
        if (this.dukascopyMerger != null) {
            this.dukascopyMerger.skipAllProgress();
        }
        this.progressListener.onError(string);
        this.closeFiles(false);
    }

    private void sendRefreshMessage() {
        try {
            SQWebSocketManager.addToDataQueue(WSDataObjects.getData(this.importInfo.symbol, "download"), "SQUANT", "QDM", "AlgoWizard");
        }
        catch (Exception exception) {
            Log.error("Cannot send data Websocket message. ", (Throwable)exception);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public synchronized void handleDownloadedMessage(GridMessage gridMessage) {
        try {
            boolean bl = gridMessage.getJobDetails().isSuccess();
            String string = gridMessage.getJobDetails().getJobID();
            DownloadResultDto downloadResultDto = (DownloadResultDto)gridMessage.getData();
            this.speedEvaluator.evalSpeed(downloadResultDto);
            if (this.stopped) {
                return;
            }
            boolean bl2 = string.endsWith("_cdn");
            if (bl2) {
                boolean bl3;
                boolean bl4 = bl3 = downloadResultDto != null && downloadResultDto.isChecksumFailed();
                if (!bl3) {
                    this.handleCdnRecords(string, downloadResultDto, bl);
                } else {
                    this.cdnError = bl3;
                }
            } else {
                this.handleBi5Data(downloadResultDto, string, bl);
            }
        }
        finally {
            this.downloadCount.decrementAndGet();
        }
    }

    private void handleBi5Data(DownloadResultDto downloadResultDto, String string, boolean bl) {
        try {
            if (!bl) {
                String string2 = this.dukascopyMerger.getDateDesc(this.dukascopyMerger.getDateForJob(string));
                Log.debug("Parsing for date:{} failed", (Object)string2);
            }
            this.dukascopyMerger.handleBi5Data(downloadResultDto, string, !this.importInfo.downloadM1Data, bl);
        }
        catch (Exception exception) {
            Log.error("Error while handling data", (Throwable)exception);
            bl = false;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private boolean performCdnData(String string, int n, long l, String string2) throws Exception {
        DataBinReaderNew dataBinReaderNew = DataBinReaderNew.getInstance((int)(this.importInfo.downloadM1Data ? 1 : 2), null);
        dataBinReaderNew.setFileName(string2);
        try {
            dataBinReaderNew.openFile();
            boolean bl = false;
            while (dataBinReaderNew.readData()) {
                VersatileData versatileData = new VersatileData();
                versatileData.time = dataBinReaderNew.tickData.time;
                versatileData.volume = dataBinReaderNew.tickData.volume * 1000000.0;
                versatileData.ask = dataBinReaderNew.tickData.ask;
                versatileData.bid = dataBinReaderNew.tickData.bid;
                versatileData.open = dataBinReaderNew.tickData.open;
                versatileData.low = dataBinReaderNew.tickData.low;
                versatileData.high = dataBinReaderNew.tickData.high;
                versatileData.close = dataBinReaderNew.tickData.close;
                this.dukascopyMerger.storeToQueue(n, versatileData);
                bl = true;
            }
            if (!bl) {
                this.dukascopyMerger.clearQueue(n);
            }
            this.dukascopyMerger.tryToSaveQueue(l);
            boolean bl2 = true;
            return bl2;
        }
        catch (Exception exception) {
            this.dukascopyMerger.resetQueue(n);
            boolean bl = false;
            return bl;
        }
        finally {
            if (string2 != null) {
                dataBinReaderNew.closeFile();
            }
        }
    }

    private void handleCdnRecords(String string, DownloadResultDto downloadResultDto, boolean bl) {
        String string2 = string.substring(0, string.length() - 4);
        Integer n = this.dukascopyMerger.getJobsIndex(string2);
        long l = this.dukascopyMerger.getDateForJob(string2);
        try {
            if (bl) {
                bl = this.performCdnData(string, n, l, downloadResultDto.getFilename());
            } else {
                bl = false;
                this.dukascopyMerger.showError(l, "Download failed. Error code: " + downloadResultDto.getHttpCode());
            }
        }
        catch (Exception exception) {
            Log.error("Error while handling response", (Throwable)exception);
            bl = false;
        }
        if (this.dukascopyMerger.isSaveError()) {
            return;
        }
        if (!bl) {
            if (this.importInfo.downloadM1Data) {
                this.errors.add(this.getJobId() + "_" + n);
                this.dukascopyMerger.register(n, l);
            } else {
                int n2 = 0;
                if (this.importInfo.ignoreWeekend && SQTime.getDayOfWeek((long)l) == 7) {
                    n2 = 19;
                }
                for (int i = n2; i < 24; ++i) {
                    this.errors.add(this.getJobId() + "_" + i);
                    this.dukascopyMerger.register(i, SQTime.addHours((long)l, (int)i));
                }
                this.dukascopyMerger.resetWithBatchAndStart(n2 - 1, 24);
            }
        }
    }

    private void executeJobsAndWait(List<GridJob<DownloadResultDto>> list) throws Exception {
        if (list.isEmpty()) {
            return;
        }
        GridClient gridClient = SQGrid.getGridClient();
        this.downloadCount.set(list.size());
        gridClient.executeOnGrid(DOWNLOAD_GROUP, list, this.executeOptions);
        this.waitForFinish();
    }

    private void waitForFinish() {
        while (this.downloadCount.get() != 0 && !this.stopped) {
            try {
                Thread.sleep(200L);
            }
            catch (InterruptedException interruptedException) {}
        }
    }

    private void downloadMissing() throws Exception {
        if (this.errors.isEmpty()) {
            return;
        }
        List<GridJob<DownloadResultDto>> list = this.generateDownloadJobs(this.errors);
        this.errors.clear();
        this.executeJobsAndWait(list);
    }

    private void finish() {
        try {
            if (this.stopped) {
                this.dukascopyMerger.setStopped(this.stopped);
            }
            this.dukascopyMerger.finish();
            long l = this.dukascopyMerger.getFromDate();
            long l2 = this.dukascopyMerger.getToDate();
            if (l != -1L && l2 != -1L) {
                String string = this.importInfo.downloadM1Data ? "M1" : "TICK";
                long l3 = string.equals("TICK") ? this.dukascopyMerger.getSavedSecs() : (long)(this.dukascopyMerger.getSavedRows() * 60);
                if (this.importInfo.rows == 0) {
                    QDM.getInstance().symbols.add(this.importInfo.origSymbol, 1, this.importInfo.downloadM1Data ? 1 : 1, this.importInfo.useCDN, SQTime.getYearsBetween((long)l, (long)l2));
                }
                DataManager.updateData((String)"History", (String)this.importInfo.symbol, (long)l, (long)l2, (int)this.dukascopyMerger.getSavedRows(), (long)l3, (int)1, (String)string, (String)this.targetTimezone);
            }
        }
        catch (Exception exception) {
            Log.error("Error while saving results", (Throwable)exception);
            throw new RuntimeException(L.t((String)"Error while saving results", (Object[])new Object[0]));
        }
    }

    private void closeFiles(boolean bl) {
        String string;
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
        String string2 = string = this.importInfo.downloadM1Data ? "M1" : "TICK";
        if (bl) {
            DukascopyUtils.deleteCopyFile(this.importInfo.symbol, string);
        } else {
            DukascopyUtils.revertCopyFile(this.importInfo.symbol, string);
        }
    }
}

