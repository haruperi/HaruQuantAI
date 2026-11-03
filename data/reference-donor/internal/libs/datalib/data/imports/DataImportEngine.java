/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.utils.IProgressListener
 *  org.joda.time.DateTimeZone
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.data.imports;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.imports.CsvFileReader;
import com.strategyquant.datalib.data.imports.CustomDataFormat;
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
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import org.joda.time.DateTimeZone;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataImportEngine {
    public static final Logger Log = LoggerFactory.getLogger(DataImportEngine.class);
    private ImportDataInfo importInfo;
    private DataInfo dataInfo;
    private DateTimeZone timeZone;
    private DataCsvLoader csvLoader;
    private static DataImportEngine instance;
    private boolean confirmed = false;
    private boolean canceled = false;
    private volatile boolean importRunning = false;
    private int rows = 0;
    private Thread importThread;
    private IProgressListener listener;

    public static void importData(String string, String string2, String string3, ImportDataInfo importDataInfo, IProgressListener iProgressListener) throws Exception {
        if (instance == null) {
            instance = new DataImportEngine();
        }
        if (DataImportEngine.instance.importRunning) {
            throw new Exception("Import is already running");
        }
        DataImportEngine.instance.listener = iProgressListener;
        DataImportEngine.instance.importInfo = importDataInfo;
        DataImportEngine.instance.dataInfo = DataManager.getDataInfo(string, string2);
        DataImportEngine.instance.timeZone = DateTimeZone.forID((String)string3);
        DataImportEngine.instance.confirmed = false;
        DataImportEngine.instance.canceled = false;
        DataImportEngine.instance.rows = 0;
        if (DataImportEngine.instance.dataInfo.rows == 0) {
            DataImportEngine.instance.dataInfo.timezone = string3;
        }
        instance.importDataFile();
    }

    public static void continueImport() {
        DataImportEngine.instance.confirmed = true;
    }

    public static void cancelImport() {
        DataImportEngine.instance.csvLoader.cancel();
        DataImportEngine.instance.canceled = true;
    }

    private void importDataFile() throws Exception {
        this.importThread = new Thread(){

            @Override
            public void run() {
                DataImportEngine.this.importRunning = true;
                DataBinWriterNew dataBinWriterNew = null;
                long l = 0L;
                int n = 0;
                try {
                    IDataLoader iDataLoader;
                    ChartDef chartDef;
                    DataImportEngine.this.listener.onStart();
                    instance.checkDataFile();
                    DataImportEngine.this.listener.setStep(2);
                    DataImportEngine.this.listener.setMessage(L.t((String)"Importing data...", (Object[])new Object[0]));
                    dataBinWriterNew = ((DataImportEngine)DataImportEngine.this).importInfo.timeframe.equals("TICK") ? DataBinWriterNew.getInstance(2, MainApp.getDataPath(), ((DataImportEngine)DataImportEngine.this).dataInfo.symbolInfo) : DataBinWriterNew.getInstance(1, MainApp.getDataPath(), ((DataImportEngine)DataImportEngine.this).dataInfo.symbolInfo);
                    String string = DataManager.getDataFileName(((DataImportEngine)DataImportEngine.this).dataInfo.connection, ((DataImportEngine)DataImportEngine.this).dataInfo.symbol, ((DataImportEngine)DataImportEngine.this).importInfo.timeframe, "No Session");
                    String string2 = DataManager.getTempFileName(string);
                    dataBinWriterNew.setFileName(string2);
                    dataBinWriterNew.open();
                    long l2 = ((DataImportEngine)DataImportEngine.this).dataInfo.dateFrom;
                    long l3 = ((DataImportEngine)DataImportEngine.this).dataInfo.dateTo;
                    long l4 = ((DataImportEngine)DataImportEngine.this).importInfo.beginTimeNewFile;
                    long l5 = ((DataImportEngine)DataImportEngine.this).importInfo.endTimeNewFile;
                    long l6 = TimeframeManager.getMillis(((DataImportEngine)DataImportEngine.this).importInfo.timeframe);
                    l6 = l6 == 0L ? 1000L : l6;
                    long l7 = l2 < l4 && l2 != 0L ? l2 : l4;
                    long l8 = l3 > l5 ? l3 : l5;
                    int n2 = (int)((l8 - l7) / l6);
                    int n3 = 0;
                    long l9 = 0L;
                    int n4 = -1;
                    int n5 = -1;
                    VersatileData versatileData = new VersatileData();
                    if (l2 < l4 && l2 != 0L) {
                        chartDef = new ChartDef(((DataImportEngine)DataImportEngine.this).dataInfo.connection, ((DataImportEngine)DataImportEngine.this).dataInfo.symbol, ((DataImportEngine)DataImportEngine.this).dataInfo.timeframe, l2, l4, 2.5, "No Session");
                        iDataLoader = DataManager.getDataLoader(chartDef, 1);
                        iDataLoader.open();
                        while (iDataLoader.hasNextTick()) {
                            iDataLoader.getNextTick(versatileData);
                            dataBinWriterNew.writeData(versatileData);
                            n5 = SQTime.getDateTime((long)versatileData.time);
                            if (n5 != n4) {
                                ++l9;
                            }
                            n4 = n5;
                            DataImportEngine.this.listener.onProgress((double)(++n3) / (double)n2 * 100.0);
                            if (!DataImportEngine.this.canceled) continue;
                            iDataLoader.close();
                            DataImportEngine.this.cancel(dataBinWriterNew, string);
                        }
                        iDataLoader.close();
                    }
                    DataImportEngine.this.csvLoader = new DataCsvLoader();
                    DataCsvLoader.reset();
                    DataImportEngine.this.csvLoader.setParams(DataImportEngine.this.importInfo, DataImportEngine.this.dataInfo, null);
                    DataImportEngine.this.csvLoader.openFile();
                    DataImportEngine.this.importInfo.resetLastAskBid();
                    while (DataImportEngine.this.csvLoader.readData()) {
                        if (!DataImportEngine.this.csvLoader.isDataCorrect()) continue;
                        DataImportEngine.this.convertToOriginalTimezone(((DataImportEngine)DataImportEngine.this).csvLoader.tickData);
                        if (((DataImportEngine)DataImportEngine.this).csvLoader.tickData.time > l) {
                            n = 0;
                        } else if (((DataImportEngine)DataImportEngine.this).csvLoader.tickData.time == l) {
                            ++n;
                        } else {
                            throw new Exception("This shouldn't happen - time on line is smaller than previous record!");
                        }
                        l = ((DataImportEngine)DataImportEngine.this).csvLoader.tickData.time;
                        if (n > 0) {
                            ((DataImportEngine)DataImportEngine.this).csvLoader.tickData.time += (long)n;
                        }
                        dataBinWriterNew.writeData(((DataImportEngine)DataImportEngine.this).csvLoader.tickData);
                        DataImportEngine.this.rows++;
                        DataImportEngine.this.listener.onProgress((double)(++n3) / (double)n2 * 100.0);
                        if (!DataImportEngine.this.canceled) continue;
                        DataImportEngine.this.csvLoader.close();
                        DataImportEngine.this.cancel(dataBinWriterNew, string);
                    }
                    DataImportEngine.this.csvLoader.close();
                    DataCsvLoader.reset();
                    if (l3 > l5) {
                        chartDef = new ChartDef(((DataImportEngine)DataImportEngine.this).dataInfo.connection, ((DataImportEngine)DataImportEngine.this).dataInfo.symbol, ((DataImportEngine)DataImportEngine.this).dataInfo.timeframe, l5, l3, 2.5, "No Session");
                        iDataLoader = DataManager.getDataLoader(chartDef, 1);
                        iDataLoader.open();
                        while (iDataLoader.hasNextTick()) {
                            iDataLoader.getNextTick(versatileData);
                            dataBinWriterNew.writeData(versatileData);
                            DataImportEngine.this.listener.onProgress((double)(++n3) / (double)n2 * 100.0);
                            if (!DataImportEngine.this.canceled) continue;
                            iDataLoader.close();
                            DataImportEngine.this.cancel(dataBinWriterNew, string);
                        }
                        iDataLoader.close();
                    }
                    DataManager.updateData(((DataImportEngine)DataImportEngine.this).dataInfo.connection, ((DataImportEngine)DataImportEngine.this).dataInfo.symbol, l7, l8, n3, l9, ((DataImportEngine)DataImportEngine.this).dataInfo.barTimeType, ((DataImportEngine)DataImportEngine.this).importInfo.timeframe, ((DataImportEngine)DataImportEngine.this).dataInfo.timezone);
                    dataBinWriterNew.close();
                    DataManager.removeDataFiles(((DataImportEngine)DataImportEngine.this).dataInfo.connection, ((DataImportEngine)DataImportEngine.this).dataInfo.symbol);
                    new File(string2).renameTo(new File(string));
                    DataImportEngine.this.importRunning = false;
                    DataImportEngine.this.listener.onProgress(100.0);
                    DataImportEngine.this.listener.onFinish();
                }
                catch (Exception exception) {
                    DataImportEngine.this.importRunning = false;
                    try {
                        DataImportEngine.this.csvLoader.close();
                        if (dataBinWriterNew != null) {
                            dataBinWriterNew.close();
                        }
                    }
                    catch (Exception exception2) {
                        Log.error("Error while closing file loader/writer.", (Throwable)exception2);
                    }
                    Log.error("Import error.", (Throwable)exception);
                    DataImportEngine.this.listener.onError(exception.getMessage());
                }
            }
        };
        this.importThread.start();
    }

    private void cancel(DataBinWriterNew dataBinWriterNew, String string) throws Exception {
        dataBinWriterNew.close();
        new File(string).delete();
        new File(DataManager.getTempFileName(string)).delete();
        throw new Exception("Import canceled");
    }

    private void checkDataFile() throws Exception {
        this.csvLoader = new DataCsvLoader();
        DataCsvLoader.reset();
        this.csvLoader.setParams(this.importInfo, this.dataInfo, null);
        this.listener.setStep(1);
        this.listener.setMessage(L.t((String)"Checking file...", (Object[])new Object[0]));
        this.importInfo = this.csvLoader.checkFile(this.listener);
        this.checkGaps();
        this.checkTimeframe();
    }

    protected void checkGaps() throws Exception {
        if (this.dataInfo.dateFrom == 0L || this.dataInfo.dateTo == 0L) {
            return;
        }
        if (this.csvLoader.beginTimeNewFile == -1L || this.csvLoader.endTimeNewFile == -1L) {
            throw new Exception(L.t((String)"Exception during import: Cannot load first and last date, bad file format?", (Object[])new Object[0]));
        }
        long l = 0L;
        long l2 = 0L;
        Log.debug("Db data date range: From " + new Date(this.dataInfo.dateFrom) + " to " + new Date(this.dataInfo.dateTo));
        Log.debug("Imported file date range: From " + new Date(this.csvLoader.beginTimeNewFile) + " to " + new Date(this.csvLoader.endTimeNewFile));
        if (this.csvLoader.endTimeNewFile < this.dataInfo.dateFrom) {
            l = this.csvLoader.endTimeNewFile / 86400000L;
            l2 = this.dataInfo.dateFrom > 0L ? this.dataInfo.dateFrom / 86400000L : l;
        } else if (this.csvLoader.beginTimeNewFile > this.dataInfo.dateTo) {
            l = this.csvLoader.beginTimeNewFile / 86400000L;
            long l3 = l2 = this.dataInfo.dateTo > 0L ? this.dataInfo.dateTo / 86400000L : l;
        }
        if (l != 0L && Math.abs(l2 - l) > 5L) {
            int n = (int)Math.abs(l2 - l);
            this.listener.onConfirm(L.t((String)"The imported data will create a gap of %d days if added to the current history data for this symbol. Do you really want to proceed with the import?", (Object[])new Object[]{n}));
            while (!this.confirmed && !this.canceled) {
                Thread.sleep(50L);
            }
            if (this.canceled) {
                throw new Exception("Import canceled");
            }
        }
        this.importInfo.beginTimeNewFile = this.csvLoader.beginTimeNewFile;
        this.importInfo.endTimeNewFile = this.csvLoader.endTimeNewFile;
    }

    private void checkTimeframe() throws Exception {
        String string = this.importInfo.timeframe;
        if (string == null) {
            String string2 = string = this.importFormatContainsBid() ? "TICK" : this.csvLoader.recognizeTimeframe();
        }
        if (string == null) {
            throw new Exception("Import file has unknown or unsupported timeframe!");
        }
        if (this.dataInfo.timeframe != null && !this.dataInfo.timeframe.equals(string)) {
            throw new Exception("Import file has different timeframe than the symbol where you want to import it!<br>Import file timeframe was recognized to " + string + ", your symbol " + this.dataInfo.symbol + " has its base data in timeframe " + this.dataInfo.timeframe + " (loaded in some previous import).<br><br>It is not possible to import " + string + " data to existing " + this.dataInfo.timeframe + " data. Please delete the existing data from this symbol or import it under a different symbol name.");
        }
        this.importInfo.timeframe = string;
    }

    private boolean importFormatContainsBid() {
        for (int i = 0; i < this.importInfo.columnTypes.size(); ++i) {
            DefaultCol defaultCol = this.importInfo.columnTypes.get(i);
            if (!defaultCol.getName().equals("Bid") && !defaultCol.getName().equals("Ask")) continue;
            return true;
        }
        return false;
    }

    public static CustomDataFormat getFileFormat(String string, ArrayList<CustomDataFormat> arrayList, CustomDataFormat customDataFormat) throws Exception {
        BufferedReader bufferedReader = null;
        String string2 = null;
        String[] stringArray = new String[25];
        String[] stringArray2 = null;
        Object var7_7 = null;
        String[] stringArray3 = null;
        String[] stringArray4 = null;
        try {
            File file = new File(string);
            bufferedReader = new BufferedReader(new FileReader(file));
            for (int i = 0; (string2 = bufferedReader.readLine()) != null && i != 25; ++i) {
                stringArray[i] = string2 = string2.trim().replaceAll(" +", " ");
            }
            ArrayList<CustomDataFormat> arrayList2 = new ArrayList<CustomDataFormat>(arrayList);
            arrayList2.add(0, customDataFormat);
            Collections.sort(arrayList2, new Comparator<CustomDataFormat>(){

                @Override
                public int compare(CustomDataFormat customDataFormat, CustomDataFormat customDataFormat2) {
                    return customDataFormat.getOrder() - customDataFormat2.getOrder();
                }
            });
            for (CustomDataFormat customDataFormat2 : arrayList2) {
                try {
                    int n;
                    stringArray3 = new String[10];
                    for (n = 0; n < 10; ++n) {
                        stringArray3[n] = stringArray[n + customDataFormat2.getSkipRows()];
                    }
                    stringArray2 = stringArray3[0].split(customDataFormat2.getSeparator());
                    if (customDataFormat2.getName().equals("MetaTrader5 Tick Data")) {
                        stringArray4 = new String[4];
                        stringArray4[0] = stringArray2[0];
                        stringArray4[1] = stringArray2[1];
                        stringArray4[2] = stringArray2[2];
                        stringArray4[3] = stringArray2.length < 4 || stringArray2[3].isBlank() ? "0" : stringArray2[3];
                    } else {
                        stringArray4 = new String[stringArray2.length - customDataFormat2.getSkipColumns()];
                        for (n = customDataFormat2.getSkipColumns(); n < stringArray2.length; ++n) {
                            stringArray4[n - customDataFormat2.getSkipColumns()] = stringArray2[n];
                        }
                    }
                    String string3 = CsvFileReader.findSeparator(stringArray3, 0);
                    if (!customDataFormat2.getSeparator().equals(string3)) {
                        throw new Exception(String.format("The format uses different value separator '%s' as recognized '%s'.", customDataFormat2.getSeparator(), string3));
                    }
                    ImportDataInfo importDataInfo = new ImportDataInfo();
                    importDataInfo.separator = customDataFormat2.getSeparator();
                    importDataInfo.skipRows = customDataFormat2.getSkipRows();
                    importDataInfo.skipCols = customDataFormat2.getSkipColumns();
                    importDataInfo.dateFormat = customDataFormat2.getDateFormat();
                    importDataInfo.timeFormat = customDataFormat2.getTimeFormat();
                    importDataInfo.columnTypes = new ArrayList<DefaultCol>(customDataFormat2.getColumns().values());
                    DataCsvLoader dataCsvLoader = new DataCsvLoader();
                    dataCsvLoader.parseLine(stringArray4, importDataInfo);
                    Log.info("Import history data - recognized file format '" + customDataFormat2.getName() + "'.");
                    return customDataFormat2;
                }
                catch (Exception exception) {
                    Log.debug("Import history data - cannot apply file format '" + customDataFormat2.getName() + "'. Reason: " + exception.getMessage(), (Throwable)exception);
                }
            }
            bufferedReader.close();
            throw new Exception("Cannot apply any predefined file format.");
        }
        catch (Exception exception) {
            Log.error("Import history data. " + exception.getMessage(), (Throwable)exception);
            throw new Exception("Import history data. " + exception.getMessage(), exception);
        }
    }

    public static void waitUntilFinished() throws InterruptedException {
        DataImportEngine.instance.importThread.join();
    }

    public static int getRowsCount() {
        return DataImportEngine.instance.rows;
    }

    private void convertToOriginalTimezone(VersatileData versatileData) {
    }
}

