/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.DataCloner
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.utils.IProgressListener
 *  com.strategyquant.lib.utils.Pair
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.exchange;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataCloner;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.lib.L;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.lib.utils.Pair;
import com.strategyquant.tradinglib.dukascopy.DukascopyBinaryMerger;
import com.strategyquant.tradinglib.dukascopy.DukascopyUtils;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.exchange.IExchange;
import com.strategyquant.tradinglib.historyData.HttpApacheManager;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class Exchange
implements IExchange {
    private static final int STATUS_CODE_TOO_MANY_REQUESTS = 429;
    private static final int RETRY_COUNT = 5;
    public static final Logger Log = LoggerFactory.getLogger(Exchange.class);
    private static final int HOUR_CONSTANT = 3600;
    protected static final int DOWNLOAD_TIMEOUT = 120;
    protected volatile boolean canceled = false;
    protected volatile boolean stopping = false;
    protected volatile boolean paused = false;
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

    public String getProduct() {
        return "SQUANTQDM";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
    }

    @Override
    public void performDownload(String string, DataManagerProgressListener dataManagerProgressListener, DataInfo dataInfo, ImportInfo importInfo) throws Exception {
        this.jobId = string;
        this.listener = dataManagerProgressListener;
        this.dataInfo = dataInfo;
        this.importInfo = importInfo;
        this.canceled = false;
        this.stopping = false;
        Log.debug("Starting download job for symbol:" + importInfo.symbol);
        try {
            this.prepareFiles();
            this.dataMerger = new DukascopyBinaryMerger(L.t((String)"Downloaded", (Object[])new Object[0]), string, 1, importInfo);
            this.dataMerger.setProgressListener(dataManagerProgressListener);
            this.dataMerger.setWriter(this.writer);
            this.dataMerger.setReader(this.reader);
            dataManagerProgressListener.setMessage(L.t((String)"Downloading...", (Object[])new Object[0]));
            Log.debug("Starting download");
            Exception exception = null;
            try {
                this.download();
            }
            catch (Exception exception2) {
                exception = exception2;
            }
            this.finish();
            this.closeFiles(true);
            this.recomputeClonedData();
            if (exception != null) {
                throw exception;
            }
        }
        catch (Exception exception) {
            Log.error(String.format("Error while performing %s data download", this.getName()), (Throwable)exception);
            this.onError(L.t((String)"Error while performing %s data download.\n%s", (Object[])new Object[]{this.getName(), exception.getMessage()}), importInfo);
            throw new Exception(L.t((String)"Error while performing %s data download.\n%s", (Object[])new Object[]{this.getName(), exception.getMessage()}));
        }
        finally {
            DataManagerDataProgress.get().removeListener(importInfo.symbol);
            Log.debug("Download job for symbol:" + importInfo.symbol + " finished");
        }
    }

    protected String doDownload(String string) {
        for (int i = 0; i < 5; ++i) {
            try {
                byte[] byArray = HttpApacheManager.getInstance().getData(string, 120);
                return new String(byArray, StandardCharsets.UTF_8);
            }
            catch (HttpApacheManager.HttpException httpException) {
                String string2 = new String(httpException.getResultBytes(), StandardCharsets.UTF_8);
                Log.info("Detected error during download. Code:{}, Content:{}.", (Object)httpException.getCode(), (Object)string2);
                if (i == 4) continue;
                this.addWaitingCycleAfterError(httpException, i + 1);
                continue;
            }
            catch (Exception exception) {
                Log.error("Error while downloading url: " + string, (Throwable)exception);
                throw new RuntimeException(L.t((String)"Error while download data", (Object[])new Object[0]), exception);
            }
        }
        throw new RuntimeException(L.t((String)"Error while download data", (Object[])new Object[0]));
    }

    private void addWaitingCycleAfterError(HttpApacheManager.HttpException httpException, int n) {
        int n2 = 5000;
        if (httpException.getCode() == 429) {
            n2 = 120000 * n;
            Log.info("Detected too many requests. Waiting for {}ms and trying again", (Object)n2);
        } else {
            Log.info("Detected http error. Waiting for {}ms and trying again", (Object)n2);
        }
        try {
            Thread.sleep(n2);
        }
        catch (InterruptedException interruptedException) {
            Log.error("", (Throwable)interruptedException);
        }
    }

    public abstract void download() throws Exception;

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
        String string = this.dataInfo.timeframe;
        if (bl) {
            DukascopyUtils.deleteCopyFile(this.importInfo.symbol, string);
        } else {
            DukascopyUtils.revertCopyFile(this.importInfo.symbol, string);
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

    protected void evaluateSpeed(long l, long l2, long l3, long l4) {
        if (l3 > 0L && l4 > 0L) {
            double d = (double)l3 * 8.0 / 1024.0 / ((double)l4 / 1000.0);
            this.avgDownloadSpeed += d;
            ++this.avgDownloadSpeedCounter;
        }
        long l5 = this.dataMerger.getPerformedDays();
        long l6 = System.currentTimeMillis();
        if (l5 != l2) {
            this.lastPerformed = l5 - l2;
        }
        double d = (double)(l6 - l) / 1000.0;
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
        long l7 = this.dataMerger.getRestDays();
        if (l7 > 0L) {
            long l8 = (long)((double)l7 * d);
            this.listener.setEstimation(this.evaluateTime(l8));
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

    @Override
    public void cancel() {
        this.canceled = true;
    }

    @Override
    public void pause() {
        this.paused = true;
    }

    @Override
    public void restart() {
        this.paused = false;
    }

    @Override
    public boolean isCanceled() {
        return this.canceled;
    }

    @Override
    public abstract IExchange clone();
}

