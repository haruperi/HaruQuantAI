/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.utils.Pair
 *  com.strategyquant.tradinglib.dukascopy.DownloadResultDto
 *  com.strategyquant.tradinglib.dukascopy.DukascopyBinaryMerger
 *  com.strategyquant.tradinglib.dukascopy.DukascopyUtils
 *  com.strategyquant.tradinglib.dukascopy.ImportInfo
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.TD.job;

import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.utils.Pair;
import com.strategyquant.tradinglib.dukascopy.DownloadResultDto;
import com.strategyquant.tradinglib.dukascopy.DukascopyBinaryMerger;
import com.strategyquant.tradinglib.dukascopy.DukascopyUtils;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import java.io.File;
import java.io.FilenameFilter;
import java.io.IOException;
import java.nio.file.Files;
import java.util.Arrays;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ImportFileJob
extends GridJob<Void> {
    private static final long serialVersionUID = 1L;
    private static final int HOURS = 24;
    public static final Logger Log = LoggerFactory.getLogger(ImportFileJob.class);
    private DataBinReaderNew reader;
    private DataBinWriterNew writer;
    private DukascopyBinaryMerger merger;
    private ImportInfo importInfo;
    private String path;
    private volatile boolean stopped;
    private volatile boolean paused;
    private DataManagerProgressListener listener;

    public ImportFileJob(ImportInfo importInfo, String path, String jobId) throws Exception {
        super(jobId, 0, null);
        this.importInfo = importInfo;
        this.path = path;
    }

    private void evalFromTo(File folder) {
        Long maxDate;
        Long minDate = this.getFolderDate(folder.getAbsolutePath(), true);
        if (minDate != null) {
            this.importInfo.dateFrom = minDate;
        }
        if ((maxDate = this.getFolderDate(folder.getAbsolutePath(), false)) != null) {
            this.importInfo.dateTo = maxDate;
        }
    }

    private Long getFolderDate(String root, boolean min) {
        File folder = new File(root);
        if (!folder.exists()) {
            return null;
        }
        Pair<Integer, Integer> minMaxYear = this.getMinMaxFromFolder(folder.getAbsolutePath());
        if (minMaxYear == null) {
            return null;
        }
        int year = min ? (Integer)minMaxYear.getA() : (Integer)minMaxYear.getB();
        Pair<Integer, Integer> minMaxMonths = this.getMinMaxFromFolder(folder.getAbsolutePath() + "\\" + String.format("%02d", year));
        if (minMaxMonths == null) {
            return min ? SQTime.toLong((int)year, (int)1, (int)1) : SQTime.toLong((int)year, (int)12, (int)31);
        }
        int month = min ? (Integer)minMaxMonths.getA() : (Integer)minMaxMonths.getB();
        Pair<Integer, Integer> minMaxDays = this.getMinMaxFromFolder(folder.getAbsolutePath() + "\\" + String.format("%02d", year) + "\\" + String.format("%02d", month));
        if (minMaxDays == null) {
            return min ? SQTime.toLong((int)year, (int)month, (int)1) : SQTime.addMonths((long)SQTime.toLong((int)year, (int)month, (int)1), (int)1);
        }
        int day = min ? (Integer)minMaxDays.getA() : (Integer)minMaxDays.getB();
        return SQTime.toLong((int)year, (int)(month + 1), (int)day);
    }

    public void messageReceived(GridMessage message) {
        super.messageReceived(message);
        switch (message.getMessageID()) {
            case 4: {
                this.stopped = true;
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

    private void finish() {
        try {
            if (this.stopped) {
                this.merger.setStopped(this.stopped);
            }
            this.merger.finish();
            long fromTime = this.merger.getFromDate();
            long toTime = this.merger.getToDate();
            DataManager.updateData((String)"History", (String)this.importInfo.symbol, (long)fromTime, (long)toTime, (int)this.merger.getSavedRows(), (long)this.merger.getSavedSecs(), (int)1, (String)"TICK", (String)"Etc/UCT");
            if (BasketOfStocksManager.getInstance() != null) {
                BasketOfStocksManager.getInstance().updateGroupsOfSymbols();
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBaskets(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            }
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
            DukascopyUtils.deleteCopyFile((String)this.importInfo.symbol, (String)"TICK");
        }
        catch (Exception e) {
            Log.error("Error while saving results", (Throwable)e);
            throw new RuntimeException(L.t((String)"Error while saving results", (Object[])new Object[0]));
        }
    }

    private String[] getSortedFolders(String folder) {
        Object[] numFolders = new File(folder).list(new FilenameFilter(){

            @Override
            public boolean accept(File dir, String name) {
                try {
                    Integer.parseInt(name);
                }
                catch (Exception e) {
                    return false;
                }
                return new File(dir, name).isDirectory();
            }
        });
        if (numFolders == null || numFolders.length == 0) {
            return null;
        }
        Arrays.sort(numFolders);
        return numFolders;
    }

    private Pair<Integer, Integer> getMinMaxFromFolder(String folder) {
        String[] numFolders = this.getSortedFolders(folder);
        String first = numFolders[0];
        String last = numFolders[numFolders.length - 1];
        return new Pair((Object)Integer.parseInt(first), (Object)Integer.parseInt(last));
    }

    private void prepareFiles() throws Exception {
        String timeFrame = "TICK";
        this.listener.setMessage(L.t((String)"Preparing data files", (Object[])new Object[0]));
        Pair readerWriter = DukascopyUtils.prepareFiles((ImportInfo)this.importInfo, (String)timeFrame);
        this.reader = (DataBinReaderNew)readerWriter.getA();
        this.writer = (DataBinWriterNew)readerWriter.getB();
    }

    public void setProgressListener(DataManagerProgressListener progressListener) {
        this.listener = progressListener;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public Void call() throws Exception {
        try {
            this.prepareFiles();
            File folder = new File(new File(this.path), this.importInfo.origSymbol);
            this.evalFromTo(folder);
            this.merger = new DukascopyBinaryMerger("Imported", this.getJobId(), 24, this.importInfo);
            this.merger.setWriter(this.writer);
            this.merger.setReader(this.reader);
            this.merger.setProgressListener(this.listener);
            if (this.listener != null) {
                this.listener.setMessage(L.t((String)"Starting import from file...", (Object[])new Object[0]));
                this.listener.onProgress(1.0);
            }
            if (!folder.exists()) {
                this.merger.setFinishProgress(L.t((String)"Completed - no data found", (Object[])new Object[0]));
                Void void_ = null;
                return void_;
            }
            String[] years = this.getSortedFolders(folder.getAbsolutePath());
            if (years != null) {
                block4: for (String year : years) {
                    if (this.stopped) break;
                    String[] months = this.getSortedFolders(folder.getAbsolutePath() + "/" + year);
                    if (months == null) continue;
                    block5: for (String month : months) {
                        String[] days;
                        if (this.stopped) continue block4;
                        for (String day : days = this.getSortedFolders(folder.getAbsolutePath() + "/" + year + "/" + month)) {
                            long date = SQTime.toLong((int)Integer.parseInt(year), (int)(Integer.parseInt(month) + 1), (int)Integer.parseInt(day));
                            this.merger.checkDate(date);
                            this.merger.reset(24);
                            for (int hour = 0; hour < 24; ++hour) {
                                String file = folder.getAbsolutePath() + "/" + year + "/" + month + "/" + day + "/" + String.format("%02d", hour) + "h_ticks.bi5";
                                String jobId = this.getJobId() + "_" + hour;
                                this.merger.register(hour, date);
                                this.handleBinaryFile(jobId, file, date);
                                date = SQTime.addHours((long)date, (int)1);
                            }
                            if (this.stopped) continue block5;
                            this.checkPaused();
                        }
                    }
                }
            }
            this.finish();
            this.merger.setFinishProgress(this.stopped ? L.t((String)"stopped", (Object[])new Object[0]) : L.t((String)"completed", (Object[])new Object[0]));
            this.sendRefreshMessage();
            String[] stringArray = null;
            return stringArray;
        }
        finally {
            DataManagerDataProgress.get().removeListener(this.importInfo.symbol);
        }
    }

    private void checkPaused() throws InterruptedException {
        if (!this.paused) {
            return;
        }
        this.listener.onPause();
        while (this.paused && !this.stopped) {
            Thread.sleep(100L);
        }
        this.listener.onContinue();
    }

    private void sendRefreshMessage() {
        try {
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)this.importInfo.symbol, (String)"import"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            Log.error("Cannot send data Websocket message. ", (Throwable)e);
        }
    }

    private void handleBinaryFile(String jobId, String file, long date) {
        byte[] data = null;
        boolean success = true;
        File fileObj = new File(file);
        try {
            data = Files.readAllBytes(fileObj.toPath());
        }
        catch (IOException e) {
            success = false;
            this.merger.showError(date, L.t((String)"File %s is missing", (Object[])new Object[]{fileObj.getAbsolutePath()}));
            Log.error("Error while reading file", (Throwable)e);
            return;
        }
        try {
            DownloadResultDto dto = DownloadResultDto.success((byte[])data, (long)0L);
            this.merger.handleBi5Data(dto, jobId, true, success);
        }
        catch (Exception e) {
            Log.error("Error while handling data", (Throwable)e);
        }
    }
}

