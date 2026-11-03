/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.datalib.data.DataCloner
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.DataCsvLoader
 *  com.strategyquant.datalib.data.io.IDataLoader
 *  com.strategyquant.datalib.data.io.ImportDataInfo
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.data.io.columns.DefaultCol
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.utils.IProgressListener
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.Files.job;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.data.DataCloner;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.DataCsvLoader;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.ImportDataInfo;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.columns.DefaultCol;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import java.io.File;
import java.util.ArrayList;
import java.util.Date;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataImporter {
    public static final Logger Log = LoggerFactory.getLogger(DataImporter.class);
    private DataCsvLoader csvLoader = new DataCsvLoader();
    private volatile boolean canceled;
    private volatile boolean paused;
    private IProgressListener listener;
    private boolean skipInvalidRows;

    public void performImport(IProgressListener listener, DataInfo dataInfo, ImportDataInfo importInfo) throws Exception {
        this.listener = listener;
        this.canceled = false;
        DataBinWriterNew writer = null;
        long loadedTimeData = 0L;
        int addedMiliseconds = 0;
        this.skipInvalidRows = true;
        File file = new File(MainApp.getDataPath() + "/importnocheck.txt");
        if (file.exists()) {
            this.skipInvalidRows = false;
        }
        Log.info(this.skipInvalidRows ? "Invalid csv rows will be ignored" : "Invalid csv rows will be proccessed");
        try {
            IDataLoader loader;
            ChartDef chartDef;
            listener.onStart();
            this.checkDataFile(listener, dataInfo, importInfo);
            listener.setStep(2);
            listener.setMessage(L.t((String)"Importing file...", (Object[])new Object[0]));
            writer = importInfo.timeframe.equals("TICK") ? DataBinWriterNew.getInstance((int)2, (String)MainApp.getDataPath(), (InstrumentInfo)dataInfo.symbolInfo) : DataBinWriterNew.getInstance((int)1, (String)MainApp.getDataPath(), (InstrumentInfo)dataInfo.symbolInfo);
            String fileName = DataManager.getDataFileName((String)dataInfo.connection, (String)dataInfo.symbol, (String)importInfo.timeframe, (String)"No Session");
            String tempFileName = DataManager.getTempFileName((String)fileName);
            writer.setFileName(tempFileName);
            writer.open();
            long oldDataDateFrom = dataInfo.dateFrom;
            long oldDataDateTo = dataInfo.dateTo;
            long newDataDateFrom = importInfo.beginTimeNewFile;
            long newDataDateTo = importInfo.endTimeNewFile;
            long tf = TimeframeManager.getMillis((String)importInfo.timeframe);
            tf = tf == 0L ? 1000L : tf;
            long from = oldDataDateFrom < newDataDateFrom && oldDataDateFrom != 0L ? oldDataDateFrom : newDataDateFrom;
            long to = newDataDateTo;
            if (newDataDateTo > 0L && oldDataDateTo > newDataDateTo) {
                to = oldDataDateTo;
            } else if (newDataDateTo < 0L && oldDataDateTo < newDataDateTo) {
                to = oldDataDateTo;
            }
            int estimatedRecordsTotal = (int)((to - from) / tf);
            int curRecord = 0;
            long secondsRecords = 0L;
            int lastData = -1;
            int tickDate = -1;
            VersatileData data = new VersatileData();
            if (oldDataDateFrom < newDataDateFrom && oldDataDateFrom != 0L) {
                chartDef = new ChartDef(dataInfo.connection, dataInfo.symbol, dataInfo.timeframe, oldDataDateFrom, newDataDateFrom, 2.5, "No Session");
                loader = DataManager.getDataLoader((ChartDef)chartDef, (int)1);
                loader.open();
                while (loader.hasNextTick() && !this.canceled) {
                    loader.getNextTick(data);
                    if (data.time >= newDataDateFrom) break;
                    writer.writeData(data);
                    tickDate = SQTime.getDateTime((long)data.time);
                    if (tickDate != lastData) {
                        ++secondsRecords;
                    }
                    lastData = tickDate;
                    this.setProgress(++curRecord, estimatedRecordsTotal);
                    listener.setMessage(L.t((String)"Copying data %s", (Object[])new Object[]{SQTime.toDateMinuteString((long)data.time)}));
                    this.checkPaused();
                }
                loader.close();
            }
            this.csvLoader = new DataCsvLoader();
            DataCsvLoader.reset();
            this.csvLoader.setParams(importInfo, dataInfo, null);
            this.csvLoader.openFile();
            importInfo.resetLastAskBid();
            while (this.csvLoader.readData() && !this.canceled) {
                if ((!this.csvLoader.isDataCorrect() || this.csvLoader.tickData.getCheckSum() == 0) && this.skipInvalidRows) {
                    Log.warn("Skipping row #{} due incorrect content: '{}'. Average price:{}", new Object[]{this.csvLoader.loadedRows + importInfo.skipRows, this.csvLoader.getCurrentLine(), this.csvLoader.getAveragePriceValue()});
                    continue;
                }
                this.convertToOriginalTimezone(this.csvLoader.tickData);
                if (this.csvLoader.tickData.time > loadedTimeData || this.csvLoader.tickData.time < 0L && this.csvLoader.tickData.time < loadedTimeData) {
                    addedMiliseconds = 0;
                } else if (this.csvLoader.tickData.time == loadedTimeData) {
                    ++addedMiliseconds;
                } else if (importInfo.errorHandling != 1) {
                    System.out.println("HERE (2)");
                    throw new Exception("This shouldn't happen - time on line is smaller than previous record!");
                }
                loadedTimeData = this.csvLoader.tickData.time;
                if (addedMiliseconds > 0) {
                    this.csvLoader.tickData.time += (long)addedMiliseconds;
                }
                writer.writeData(this.csvLoader.tickData);
                tickDate = SQTime.getDateTime((long)this.csvLoader.tickData.time);
                if (tickDate != lastData) {
                    ++secondsRecords;
                }
                lastData = tickDate;
                this.setProgress(++curRecord, estimatedRecordsTotal);
                listener.setMessage(L.t((String)"Imported file data %s", (Object[])new Object[]{SQTime.toDateMinuteString((long)loadedTimeData)}));
                this.checkPaused();
            }
            this.csvLoader.close();
            DataCsvLoader.reset();
            if (oldDataDateTo > newDataDateTo && oldDataDateTo != 0L) {
                chartDef = new ChartDef(dataInfo.connection, dataInfo.symbol, dataInfo.timeframe, newDataDateTo, oldDataDateTo, 2.5, "No Session");
                loader = DataManager.getDataLoader((ChartDef)chartDef, (int)1);
                loader.open();
                while (loader.hasNextTick() && !this.canceled) {
                    loader.getNextTick(data);
                    writer.writeData(data);
                    tickDate = SQTime.getDateTime((long)data.time);
                    if (tickDate != lastData) {
                        ++secondsRecords;
                    }
                    lastData = tickDate;
                    this.setProgress(++curRecord, estimatedRecordsTotal);
                    listener.setMessage(L.t((String)"Imported file data %s", (Object[])new Object[]{SQTime.toDateMinuteString((long)data.time)}));
                    this.checkPaused();
                }
                loader.close();
            }
            if (!importInfo.timeframe.equals("TICK")) {
                secondsRecords = curRecord * 60;
            }
            DataManager.updateData((String)dataInfo.connection, (String)dataInfo.symbol, (long)from, (long)to, (int)curRecord, (long)secondsRecords, (int)dataInfo.barTimeType, (String)importInfo.timeframe, (String)importInfo.timezone);
            try {
                TimeframeManager.addTimeframe((String)importInfo.timeframe);
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getTimeframes(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            }
            catch (Exception exception) {
                // empty catch block
            }
            writer.close();
            DataManager.removeDataFiles((String)dataInfo.connection, (String)dataInfo.symbol);
            new File(tempFileName).renameTo(new File(fileName));
            this.recomputeClonedData(dataInfo);
            listener.onProgress(100.0);
            listener.onFinish();
        }
        catch (Exception e) {
            try {
                this.csvLoader.close();
                if (writer != null) {
                    writer.close();
                }
            }
            catch (Exception e1) {
                Log.error("Error while closing file loader/writer.", (Throwable)e1);
            }
            Log.error("Import error.", (Throwable)e);
            throw new Exception("Import error." + e.getMessage(), e);
        }
    }

    public void setProgress(int curRecord, int estimatedRecordsTotal) {
        double progress = (double)curRecord / (double)estimatedRecordsTotal * 100.0;
        if (progress > 99.0) {
            progress = 99.0;
        }
        this.listener.onProgress(progress);
    }

    private void recomputeClonedData(DataInfo dataInfo) throws Exception {
        try {
            DataCloner cloner = new DataCloner();
            DataInfo info = DataManager.getDataInfo((String)"History", (String)dataInfo.symbol);
            ArrayList clonedDataInfo = DataManager.listCloned((int)info.id);
            for (int i = 0; i < clonedDataInfo.size(); ++i) {
                DataInfo cloneInfo = (DataInfo)clonedDataInfo.get(i);
                DataManager.clearData((String)cloneInfo.connection, (String)cloneInfo.symbol);
                this.listener.setMessage(L.t((String)"Recomputing cloned data", (Object[])new Object[0]));
                String[] items = cloneInfo.timezone.split("\\|");
                String timezone = items[0];
                int hours = 0;
                try {
                    hours = Integer.parseInt(items[1]);
                }
                catch (Exception exception) {
                    // empty catch block
                }
                cloner.cloneToTimezone(dataInfo.symbol, cloneInfo.symbol, timezone, hours, cloneInfo.removeWeekends, null, this.listener);
            }
        }
        catch (Exception e) {
            Log.error("Error while recomputing cloned data.", (Throwable)e);
            throw new Exception("Error while recomputing cloned data.", e);
        }
    }

    private void convertToOriginalTimezone(VersatileData tickData) {
    }

    private void checkDataFile(IProgressListener listener, DataInfo dataInfo, ImportDataInfo importInfo) throws Exception {
        this.csvLoader = new DataCsvLoader();
        DataCsvLoader.reset();
        this.csvLoader.setParams(importInfo, dataInfo, null);
        listener.setStep(1);
        listener.setMessage(L.t((String)"Checking file for import...", (Object[])new Object[0]));
        importInfo = this.csvLoader.checkFile(listener);
        this.checkGaps(listener, dataInfo, importInfo);
        this.checkTimeframe(listener, dataInfo, importInfo);
    }

    protected void checkGaps(IProgressListener listener, DataInfo dataInfo, ImportDataInfo importInfo) throws Exception {
        if (dataInfo.dateFrom == 0L || dataInfo.dateTo == 0L) {
            return;
        }
        if (this.csvLoader.beginTimeNewFile == -1L || this.csvLoader.endTimeNewFile == -1L) {
            throw new Exception("Exception during import: Cannot load first and last date, bad file format?");
        }
        long boundaryDaysFile = 0L;
        long boundaryDaysDb = 0L;
        Log.debug("Db data date range: From " + new Date(dataInfo.dateFrom) + " to " + new Date(dataInfo.dateTo));
        Log.debug("Imported file date range: From " + new Date(this.csvLoader.beginTimeNewFile) + " to " + new Date(this.csvLoader.endTimeNewFile));
        if (this.csvLoader.endTimeNewFile < dataInfo.dateFrom) {
            boundaryDaysFile = this.csvLoader.endTimeNewFile / 86400000L;
            boundaryDaysDb = dataInfo.dateFrom > 0L ? dataInfo.dateFrom / 86400000L : boundaryDaysFile;
        } else if (this.csvLoader.beginTimeNewFile > dataInfo.dateTo) {
            boundaryDaysFile = this.csvLoader.beginTimeNewFile / 86400000L;
            long l = boundaryDaysDb = dataInfo.dateTo > 0L ? dataInfo.dateTo / 86400000L : boundaryDaysFile;
        }
        if (boundaryDaysFile != 0L && Math.abs(boundaryDaysDb - boundaryDaysFile) > 5L) {
            int days = (int)Math.abs(boundaryDaysDb - boundaryDaysFile);
            listener.onConfirm("The imported data will create a gap of " + days + " days if added to the current history data for this symbol. Do you really want to proceed with the import?");
        }
        importInfo.beginTimeNewFile = this.csvLoader.beginTimeNewFile;
        importInfo.endTimeNewFile = this.csvLoader.endTimeNewFile;
    }

    private void checkTimeframe(IProgressListener listener, DataInfo dataInfo, ImportDataInfo importInfo) throws Exception {
        String importFileTF = importInfo.timeframe;
        if (importFileTF == null) {
            String string = importFileTF = this.importFormatContainsBid(importInfo) ? "TICK" : this.csvLoader.recognizeTimeframe();
        }
        if (importFileTF == null) {
            throw new Exception("Import file has unknown or unsupported timeframe!");
        }
        if (dataInfo.timeframe != null && !dataInfo.timeframe.equals(importFileTF)) {
            throw new Exception("Import file has different timeframe than the symbol where you want to import it!<br>Import file timeframe was recognized to " + importFileTF + ", your symbol " + dataInfo.symbol + " has its base data in timeframe " + dataInfo.timeframe + " (loaded in some previous import).<br><br>It is not possible to import " + importFileTF + " data to existing " + dataInfo.timeframe + " data. Please delete the existing data from this symbol or import it under a different symbol name.");
        }
        importInfo.timeframe = importFileTF;
    }

    private boolean importFormatContainsBid(ImportDataInfo importInfo) {
        for (int i = 0; i < importInfo.columnTypes.size(); ++i) {
            DefaultCol col = (DefaultCol)importInfo.columnTypes.get(i);
            if (!col.getName().equals("Bid") && !col.getName().equals("Ask")) continue;
            return true;
        }
        return false;
    }

    private void checkPaused() throws InterruptedException {
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
        if (this.csvLoader != null) {
            this.csvLoader.cancel();
        }
        this.canceled = true;
    }

    public boolean isCanceled() {
        return this.canceled;
    }

    public void pause() {
        this.paused = true;
        if (this.csvLoader != null) {
            this.csvLoader.pause();
        }
    }

    public void restart() {
        this.paused = false;
        if (this.csvLoader != null) {
            this.csvLoader.restart();
        }
    }
}

