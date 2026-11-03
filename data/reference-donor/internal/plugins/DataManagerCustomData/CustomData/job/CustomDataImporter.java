/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.CustomDataBinWriter
 *  com.strategyquant.datalib.customData.CustomDataInfo
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  com.strategyquant.datalib.data.io.ImportDataInfo
 *  com.strategyquant.datalib.data.io.columns.DefaultCol
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.utils.IProgressListener
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataManager.impl.CustomData.job;

import com.strategyquant.datalib.customData.CustomDataBinWriter;
import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.datalib.data.io.ImportDataInfo;
import com.strategyquant.datalib.data.io.columns.DefaultCol;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.plugin.DataManager.impl.CustomData.job.CustomDataCsvLoader;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CustomDataImporter {
    public static final Logger Log = LoggerFactory.getLogger(CustomDataImporter.class);
    private volatile boolean canceled;
    private volatile boolean paused;
    CustomDataCsvLoader csvLoader = null;
    CustomDataBinWriter writer = null;
    private IProgressListener listener;

    public void performImport(IProgressListener listener, CustomDataInfo dataInfo, ImportDataInfo importInfo) throws Exception {
        this.listener = listener;
        this.canceled = false;
        this.paused = false;
        try {
            listener.onStart();
            listener.setStep(1);
            listener.setMessage(L.t((String)"Checking file...", (Object[])new Object[0]));
            double totalRows = this.checkDataFile(listener, dataInfo, importInfo);
            listener.setStep(2);
            listener.setMessage(L.t((String)"Importing file...", (Object[])new Object[0]));
            this.csvLoader = new CustomDataCsvLoader(listener, dataInfo, importInfo);
            this.csvLoader.openFile();
            this.writer = new CustomDataBinWriter();
            String fileName = CustomDataManager.getDataFileName((String)dataInfo.name);
            String tempFileName = CustomDataImporter.getTempFileName(fileName);
            this.writer.setFileName(tempFileName);
            this.writer.open();
            while (this.csvLoader.readData() && !this.canceled) {
                this.writer.writeData(this.csvLoader.loadedData);
                listener.onProgress((double)this.csvLoader.loadedRows / totalRows * 100.0);
                listener.setMessage(L.t((String)"Imported custom data %s", (Object[])new Object[]{SQTime.toDateMinuteString((long)this.csvLoader.loadedData.time)}));
                this.checkPaused();
            }
            this.csvLoader.close();
            this.writer.close();
            String tf = this.csvLoader.recognizeTimeframe();
            CustomDataManager.updateData((String)dataInfo.name, (long)this.csvLoader.fromDate, (long)this.csvLoader.toDate, (int)this.csvLoader.loadedRows, (String)tf);
            CustomDataManager.removeDataFile((String)dataInfo.name);
            new File(tempFileName).renameTo(new File(fileName));
        }
        catch (Exception e) {
            try {
                this.csvLoader.close();
                if (this.writer != null) {
                    this.writer.close();
                }
            }
            catch (Exception e1) {
                Log.error("Error while closing file loader/writer.", (Throwable)e1);
            }
            Log.error("Import error.", (Throwable)e);
            throw new Exception("Import error." + e.getMessage(), e);
        }
    }

    public static String getTempFileName(String fileName) {
        int dotPos = fileName.indexOf(".");
        String part1 = fileName.substring(0, fileName.indexOf("."));
        String part2 = fileName.substring(dotPos);
        return part1 + "_temp" + part2;
    }

    private int checkDataFile(IProgressListener listener, CustomDataInfo dataInfo, ImportDataInfo importInfo) throws Exception {
        int totalRows = this.countRows(importInfo.filePath);
        int valuesCount = 0;
        for (int i = 0; i < importInfo.columnTypes.size(); ++i) {
            if (((DefaultCol)importInfo.columnTypes.get(i)).getDataType() != 9999) continue;
            ++valuesCount;
        }
        if (dataInfo.values != valuesCount) {
            throw new Exception(L.t((String)"Wrong number of values(columns) %d <> %d.", (Object[])new Object[]{dataInfo.values, valuesCount}));
        }
        return totalRows;
    }

    public int countRows(String importFileName) {
        try {
            BufferedReader reader = new BufferedReader(new FileReader(new File(importFileName)));
            String line = null;
            int rows = 0;
            while (true) {
                try {
                    line = reader.readLine();
                }
                catch (IOException ex) {
                    Log.error("Exception", (Throwable)ex);
                }
                if (line == null) break;
                ++rows;
            }
            reader.close();
            return rows;
        }
        catch (IOException ex) {
            Log.error("Exception", (Throwable)ex);
            return -1;
        }
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

