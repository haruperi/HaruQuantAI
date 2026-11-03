/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.broker.BrokerDto
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.data.DataCloner
 *  com.strategyquant.datalib.data.DataManager
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
package com.strategyquant.tradinglib.darwinex;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.data.DataCloner;
import com.strategyquant.datalib.data.DataManager;
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
import com.strategyquant.tradinglib.historyData.DownloadMessageHandler;
import com.strategyquant.tradinglib.historyData.HttpApacheManager;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import java.io.FilterInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
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

public class DarwinexDownloadJob
extends GridJob<Void> {
    private static final int HOUR_CONSTANT = 3600;
    private static final int MAX_M1_DOWNLOAD_PARALLEL = 3;
    public static final String DOWNLOAD_GROUP = "DarwinexDownloadPerformerGroup";
    private static final long serialVersionUID = 1L;
    public static final Logger Log = LoggerFactory.getLogger(DarwinexDownloadJob.class);
    private ImportInfo importInfo;
    private DukascopyBinaryMerger dukascopyMerger;
    private DataBinReaderNew reader;
    private DataBinWriterNew writer;
    private long currentDateTime = -1L;
    private DataManagerProgressListener progressListener;
    private volatile boolean stopped;
    private volatile boolean cdnError;
    private long endDateTime;
    private volatile boolean paused;
    private volatile AtomicInteger downloadCount = new AtomicInteger();
    private long lastPerformed = 0L;
    private CdnCache cdnCache;
    private ExecuteOptions executeOptions;
    private SpeedEvaluator speedEvaluator = new SpeedEvaluator();
    private DownloadMessageHandler downloadMessageHandler;
    private String targetTimezone = "Etc/UCT";
    private DataInfo dataInfo;
    private Future<?> preloadFuture;
    private String cdnUrl;

    public DarwinexDownloadJob(String string, String string2, ImportInfo importInfo) throws Exception {
        super(string2, 0, null);
        this.cdnUrl = string;
        this.importInfo = importInfo;
        this.executeOptions = new ExecuteOptions();
        this.executeOptions.setMaxRunningCount(6);
        this.currentDateTime = SQTime.correctDayStart((long)importInfo.dateFrom);
        this.endDateTime = SQTime.correctDayStart((long)importInfo.dateTo);
        long l = SQTime.correctDayStart((long)System.currentTimeMillis());
        if (this.endDateTime >= l) {
            this.endDateTime = SQTime.addDays((long)this.endDateTime, (int)-1);
        }
        this.downloadMessageHandler = new DownloadMessageHandler(){

            @Override
            public void onDownloadMessage(String string, String string2) {
                DarwinexDownloadJob.this.progressListener.setMessage(string);
                if (string2 != null) {
                    DarwinexDownloadJob.this.progressListener.setSpeed(string2);
                }
            }
        };
        this.dataInfo = DataManager.getDataInfo((String)"History", (String)importInfo.symbol);
    }

    private void handleBroker() {
        if (this.dataInfo.brokerId != -1) {
            String string;
            BrokerDto brokerDto = BrokerManager.getInstance().getBroker(Integer.valueOf(this.dataInfo.brokerId));
            this.targetTimezone = string = brokerDto.getMtTimezone();
            this.dukascopyMerger.setTargetTimezone(this.targetTimezone);
        }
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
        Pair<DataBinReaderNew, DataBinWriterNew> pair = DukascopyUtils.prepareFiles(this.importInfo, "TICK");
        this.reader = (DataBinReaderNew)pair.getA();
        this.writer = (DataBinWriterNew)pair.getB();
    }

    public void setProgressListener(DataManagerProgressListener dataManagerProgressListener) {
        this.progressListener = dataManagerProgressListener;
    }

    private List<GridJob<DownloadResultDto>> generateDownloadJobs() throws Exception {
        int n;
        int n2;
        LinkedList<GridJob<DownloadResultDto>> linkedList = new LinkedList<GridJob<DownloadResultDto>>();
        if (this.currentDateTime > this.endDateTime) {
            return linkedList;
        }
        this.currentDateTime = this.dukascopyMerger.checkDate(this.currentDateTime);
        if (this.currentDateTime > this.endDateTime) {
            return linkedList;
        }
        int n3 = n2 = this.importInfo.downloadM1Data ? 3 : 1;
        for (n = 0; this.currentDateTime <= this.endDateTime && n < n2; ++n) {
            String string = this.getJobId() + "_" + n + "_cdn";
            int n4 = SQTime.getFullYear((long)this.currentDateTime);
            int n5 = SQTime.getMonth((long)this.currentDateTime) + 1;
            int n6 = SQTime.getDay((long)this.currentDateTime);
            linkedList.add(new CdnDownloadJob(string, this.cdnCache, n4, n5, n6, 0, this.downloadMessageHandler));
            this.dukascopyMerger.register(n, this.currentDateTime);
            this.currentDateTime = SQTime.addDays((long)this.currentDateTime, (int)1);
        }
        this.dukascopyMerger.reset(n);
        return linkedList;
    }

    public void messageReceived(GridMessage gridMessage) {
        super.messageReceived(gridMessage);
        switch (gridMessage.getMessageID()) {
            case 4: {
                this.stopped = true;
                this.progressListener.setMessage(L.t((String)"Stopping download - please wait", (Object[])new Object[0]));
                this.cdnCache.stop();
                if (this.preloadFuture == null) break;
                this.preloadFuture.cancel(true);
                break;
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

    private void loadCheckSumsForCDN() throws Exception {
        int n;
        this.progressListener.setMessage(L.t((String)"Loading symbol's checksums", (Object[])new Object[0]));
        String string = this.cdnUrl;
        int n2 = string.indexOf("/", 10);
        Log.info("Downloading {} from server: {}", (Object)this.importInfo.origSymbol, (Object)string.substring(0, n2));
        String string2 = string + "/" + this.importInfo.origSymbol + "/metadata.dat";
        HttpClient httpClient = HttpApacheManager.getInstance().getClient();
        HttpGet httpGet = new HttpGet(string2);
        int n3 = -1;
        int n4 = -1;
        HashSet<String> hashSet = new HashSet<String>();
        FilterInputStream filterInputStream = null;
        try {
            HttpResponse httpResponse = httpClient.execute((HttpUriRequest)httpGet);
            httpResponse.getEntity().getContent();
            HttpEntity httpEntity = httpResponse.getEntity();
            InputStream inputStream = httpEntity.getContent();
            byte[] byArray = IOUtils.toByteArray((InputStream)inputStream);
            String string3 = new String(byArray, "UTF-8");
            String[] stringArray = string3.split(";");
            if (stringArray != null) {
                for (String string4 : stringArray) {
                    if ((string4 = string4.trim()).isEmpty()) continue;
                    hashSet.add(string4);
                    try {
                        String string5 = string4.substring(0, string4.length() - 4);
                        Integer n5 = Integer.valueOf(string5);
                        if (n3 == -1 || n5 < n3) {
                            n3 = n5;
                        }
                        if (n5 <= n4) continue;
                        n4 = n5;
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                }
            }
        }
        catch (Exception exception) {
            Log.error("Error while loading CDN database from url:" + string2, (Throwable)exception);
            throw exception;
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
        int n6 = SQTime.getFullYear((long)this.currentDateTime);
        if (n6 < n3) {
            this.currentDateTime = SQTime.toLong((int)n3, (int)1, (int)1, (int)0, (int)0, (int)0);
        }
        if (n4 < (n = SQTime.getFullYear((long)this.endDateTime))) {
            this.endDateTime = SQTime.toLong((int)n4, (int)12, (int)31, (int)23, (int)59, (int)0);
        }
        this.cdnCache = new CdnCache(this.getJobId(), string, this.importInfo.origSymbol, hashSet, this.currentDateTime);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public Void call() throws Exception {
        try {
            long l;
            this.progressListener.onProgress(0.1);
            this.progressListener.setMessage(L.t((String)"Waiting in queue", (Object[])new Object[0]));
            Log.debug("Starting download job for symbol:" + this.importInfo.symbol);
            this.dukascopyMerger = new DukascopyBinaryMerger("Writing ", this.getJobId(), 1, this.importInfo);
            this.dukascopyMerger.setProgressListener(this.progressListener);
            this.dukascopyMerger.setIgnoreWeekend(this.importInfo.ignoreWeekend);
            this.handleBroker();
            if (this.stopped) {
                this.dukascopyMerger.setFinishProgress("Stopped");
                this.sendRefreshMessage();
                Void void_ = null;
                return void_;
            }
            this.loadCheckSumsForCDN();
            this.progressListener.setDownloadType(L.t((String)"Fast download", (Object[])new Object[0]));
            this.progressListener.setDataType(L.t((String)"Tick data", (Object[])new Object[0]));
            this.prepareFiles();
            this.dukascopyMerger.setWriter(this.writer);
            this.dukascopyMerger.setReader(this.reader);
            this.progressListener.setMessage(L.t((String)"Downloading...", (Object[])new Object[0]));
            Log.debug("Starting download");
            if (this.cdnCache != null) {
                ExecutorService executorService = Executors.newSingleThreadExecutor();
                try {
                    this.preloadFuture = executorService.submit(() -> this.cdnCache.preload(this.currentDateTime, this.endDateTime, this.downloadMessageHandler));
                    this.preloadFuture.get();
                }
                catch (CancellationException cancellationException) {
                    // empty catch block
                }
                this.preloadFuture = null;
            }
            long l2 = System.currentTimeMillis();
            while (!this.stopped && !this.cdnError) {
                l = this.dukascopyMerger.getPerformedDays();
                long l3 = System.currentTimeMillis();
                List<GridJob<DownloadResultDto>> list = this.generateDownloadJobs();
                Log.debug("Generating downloads jobs:" + list.size());
                if (list.isEmpty()) break;
                this.executeJobsAndWait(list);
                if (this.stopped) break;
                this.checkPaused();
                this.evaluateSpeed(l3, l);
                if (!this.importInfo.downloadM1Data || this.reader == null) continue;
                this.dukascopyMerger.readTill(this.currentDateTime, false);
            }
            this.finish();
            this.closeFiles(true);
            this.recomputeClonedData();
            if (this.cdnError) {
                this.onError("Download problem - check your internet connection");
            } else {
                l = (System.currentTimeMillis() - l2) / 1000L;
                String string = this.stopped ? "Stopped" : "Completed";
                this.dukascopyMerger.setFinishProgress(string + " in " + this.evaluateTime(l));
            }
            this.sendRefreshMessage();
        }
        catch (Exception exception) {
            Log.error("Error while performing darwinex download", (Throwable)exception);
            this.onError("Error while performing darwinex download");
        }
        finally {
            if (this.cdnCache != null) {
                this.cdnCache.clean();
            }
            DataManagerDataProgress.get().removeListener(this.importInfo.symbol);
            Log.debug("Download job for symbol:" + this.importInfo.symbol + " finished");
        }
        return null;
    }

    private void evaluateSpeed(long l, long l2) {
        long l3 = this.dukascopyMerger.getPerformedDays();
        long l4 = System.currentTimeMillis();
        if (l3 != l2) {
            this.lastPerformed = l3 - l2;
        }
        double d = (double)(l4 - l) / 1000.0;
        double d2 = (double)this.lastPerformed / d;
        double d3 = (double)Math.round(d2 * 10.0) / 10.0;
        String string = " (" + d3 + " days/sec) - " + this.speedEvaluator.getSpeed();
        this.progressListener.setSpeed(string);
        this.speedEvaluator.reset();
        long l5 = this.dukascopyMerger.getRestDays();
        if (l5 > 0L) {
            long l6 = (long)((double)l5 * d);
            this.progressListener.setEstimation(this.evaluateTime(l6));
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
            this.onError("Error while recomputing cloned data.");
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
            this.handleCdnRecords(string, downloadResultDto, bl);
        }
        finally {
            this.downloadCount.decrementAndGet();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private boolean performCdnData(String string, int n, long l, String string2) throws Exception {
        DataBinReaderNew dataBinReaderNew = DataBinReaderNew.getInstance((int)2, null);
        dataBinReaderNew.setFileName(string2);
        dataBinReaderNew.openFile();
        try {
            boolean bl = false;
            while (dataBinReaderNew.readData()) {
                VersatileData versatileData = new VersatileData();
                versatileData.time = dataBinReaderNew.tickData.time;
                versatileData.volume = dataBinReaderNew.tickData.volume;
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
            this.dukascopyMerger.clearQueue(n);
            boolean bl = false;
            return bl;
        }
        finally {
            dataBinReaderNew.closeFile();
        }
    }

    private void handleCdnRecords(String string, DownloadResultDto downloadResultDto, boolean bl) {
        String string2 = string.substring(0, string.length() - 4);
        Integer n = this.dukascopyMerger.getJobsIndex(string2);
        long l = this.dukascopyMerger.getDateForJob(string2);
        try {
            if (bl && downloadResultDto.getFilename() != null) {
                bl = this.performCdnData(string, n, l, downloadResultDto.getFilename());
            } else {
                if (!bl) {
                    this.dukascopyMerger.showError(l, "Download failed. Error code: " + downloadResultDto.getHttpCode());
                }
                this.dukascopyMerger.updateProgress("No data for date: " + SQTime.toString((long)l, (String)"yyyy.MM.dd"), false);
                bl = false;
            }
        }
        catch (Exception exception) {
            Log.error("Error while handling response", (Throwable)exception);
            bl = false;
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

    private void finish() {
        try {
            if (this.stopped) {
                this.dukascopyMerger.setStopped(this.stopped);
            }
            this.dukascopyMerger.finish();
            long l = this.dukascopyMerger.getFromDate();
            long l2 = this.dukascopyMerger.getToDate();
            if (l != -1L && l2 != -1L) {
                long l3 = this.dukascopyMerger.getSavedSecs();
                if (this.importInfo.rows == 0) {
                    QDM.getInstance().symbols.add(this.importInfo.origSymbol, 1, this.importInfo.downloadM1Data ? 1 : 1, this.importInfo.useCDN, SQTime.getYearsBetween((long)l, (long)l2));
                }
                DataManager.updateData((String)"History", (String)this.importInfo.symbol, (long)l, (long)l2, (int)this.dukascopyMerger.getSavedRows(), (long)l3, (int)1, (String)"TICK", (String)this.targetTimezone);
            }
        }
        catch (Exception exception) {
            Log.error("Error while saving results", (Throwable)exception);
            throw new RuntimeException(L.t((String)"Error while saving results", (Object[])new Object[0]));
        }
    }

    private void closeFiles(boolean bl) {
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
            DukascopyUtils.deleteCopyFile(this.importInfo.symbol, "TICK");
        } else {
            DukascopyUtils.revertCopyFile(this.importInfo.symbol, "TICK");
        }
    }
}

