/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.utils.IProgressListener
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.data.io;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.io.AbstractDataCsvLoader;
import com.strategyquant.datalib.data.io.ImportDataInfo;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.columns.DefaultCol;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.utils.IProgressListener;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.UUID;
import javax.swing.JProgressBar;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataCsvLoader
extends AbstractDataCsvLoader {
    public static final Logger Log = LoggerFactory.getLogger(DataCsvLoader.class);
    public long beginTimeNewFile = -1L;
    public long endTimeNewFile = -1L;
    private double averagePriceValue = 0.0;
    public final VersatileData tickData = new VersatileData();
    private String currentLine;

    public DataCsvLoader() {
        this.df = null;
        this.timeColumn = 0;
        this.isTimeCol = false;
    }

    public void setParams(ImportDataInfo importDataInfo, DataInfo dataInfo, JProgressBar jProgressBar) {
        this.importInfo = importDataInfo;
        this.progressBar = jProgressBar;
        this.dataInfo = dataInfo;
    }

    public ImportDataInfo checkFile(IProgressListener iProgressListener) throws Exception {
        this.beginTimeNewFile = -1L;
        this.listener = iProgressListener;
        this.loadedRows = 0;
        long l = new File(this.importInfo.filePath).length();
        this.previousTime = 0L;
        this.progressPercent = 0.0;
        this.cancel = false;
        this.openFile();
        String string = null;
        String[] stringArray = null;
        int n = this.importInfo.columnTypes.size();
        String[] stringArray2 = new String[n];
        this.tfRecognizer.reset();
        boolean bl = true;
        boolean bl2 = false;
        this.importInfo.resetLastAskBid();
        long l2 = 0L;
        while (!this.cancel) {
            this.checkPaused();
            if (this.rows == 0 && this.importInfo.skipRows > 0) {
                for (int i = 0; i < this.importInfo.skipRows; ++i) {
                    String string2 = this.readLine();
                    l2 += (long)string2.length();
                }
            }
            string = this.readLine();
            if (bl) {
                bl2 = string.replaceAll("( +)", " ").trim().length() < string.length();
                bl = false;
            }
            if (string == null) break;
            l2 += (long)string.length();
            if (iProgressListener != null) {
                this.progressPercent = (double)l2 / (double)l * 100.0;
                iProgressListener.onProgress(this.progressPercent);
                iProgressListener.setMessage("Checking row #" + this.loadedRows);
            }
            if (bl2) {
                string = string.replaceAll("( +)", " ").trim();
            }
            try {
                stringArray = string.split(this.importInfo.separator);
                if (this.importInfo.isMT5TickImport() && (stringArray = this.importInfo.correctMT5TickData(stringArray)) == null) continue;
                ++this.loadedRows;
                if (this.importInfo.skipCols > 0) {
                    if (stringArray.length - this.importInfo.skipCols <= 0) {
                        throw new Exception("There are less columns than specified in Skip Columns parameter!");
                    }
                    if (stringArray.length - this.importInfo.skipCols < n) {
                        throw new Exception(String.format("There are not enough data columns in the file! Found: %d, Required: %d", stringArray.length - this.importInfo.skipCols, n));
                    }
                    stringArray2 = Arrays.copyOfRange(stringArray, this.importInfo.skipCols, stringArray.length);
                } else {
                    stringArray2 = stringArray;
                }
                Object[] objectArray = this.parseLine(stringArray2, this.importInfo);
                this.parseTickData(objectArray);
                if (this.loadedRows < 100 && this.tickData.ask != 0.0 && this.tickData.bid != 0.0 && this.tickData.bid > this.tickData.ask) {
                    throw new Exception("Bid cannot be bigger than Ask, please check your columns!");
                }
                if (this.tickData.time == Long.MIN_VALUE) {
                    throw new Exception("Cannot recognize date and time!");
                }
                if (this.tickData.time > 0L && this.tickData.time < this.previousTime) {
                    if (this.importInfo.errorHandling == 1) {
                        Log.error(String.format("Error parsing on row: %d, line contents: %s, message: %s", this.rows, string, "Invalid time consecution. Each row must have same or latter time than the previous one"));
                    } else {
                        throw new Exception("Invalid time consecution. Each row must have same or latter time than the previous one");
                    }
                }
                if (this.loadedRows < 100000) {
                    this.tfRecognizer.processTime(this.tickData.time);
                }
                this.previousTime = this.tickData.time;
                if (this.beginTimeNewFile == -1L) {
                    this.beginTimeNewFile = this.tickData.time;
                }
                this.endTimeNewFile = this.tickData.time;
            }
            catch (Exception exception) {
                if (this.importInfo.errorHandling == 1) {
                    Log.debug(String.format("[checking_data] Skipping row %d, line: %s, reason: %s", this.loadedRows, string, exception.getMessage()));
                    continue;
                }
                throw new Exception(String.format("Error parsing on row: %d, line contents: %s, message: %s", this.loadedRows, string, exception.getMessage()), exception);
            }
        }
        if (this.cancel && iProgressListener != null) {
            throw new Exception("File check canceled");
        }
        this.close();
        if (this.beginTimeNewFile > this.endTimeNewFile) {
            long l3 = this.beginTimeNewFile;
            this.beginTimeNewFile = this.endTimeNewFile;
            this.endTimeNewFile = l3;
            this.reverseFile(this.importInfo);
        }
        this.importInfo.importFileRows = this.rows;
        this.importInfo.beginTimeNewFile = this.beginTimeNewFile;
        this.importInfo.endTimeNewFile = this.endTimeNewFile;
        Log.info("Imported " + this.loadedRows + " rows");
        return this.importInfo;
    }

    private ImportDataInfo reverseFile(ImportDataInfo importDataInfo) throws Exception {
        Log.info("File in reverse order, reversing to temporary file");
        String string = MainApp.getDataPath() + "/internal/tmp/" + UUID.randomUUID().toString() + ".txt";
        this.openFile();
        String string2 = null;
        ArrayList<String> arrayList = new ArrayList<String>();
        while (true) {
            if (this.rows == 0 && importDataInfo.skipRows > 0) {
                for (int i = 0; i < importDataInfo.skipRows; ++i) {
                    this.readLine();
                }
            }
            string2 = this.readLine();
            if (this.progressBar != null) {
                this.progressBar.setValue(this.rows);
            }
            if (string2 == null) break;
            ++this.loadedRows;
            arrayList.add(string2);
        }
        this.close();
        Collections.reverse(arrayList);
        PrintWriter printWriter = new PrintWriter(new BufferedWriter(new FileWriter(string, StandardCharsets.UTF_8)));
        for (String string3 : arrayList) {
            printWriter.println(string3);
        }
        printWriter.close();
        importDataInfo.filePath = string;
        importDataInfo.skipRows = 0;
        importDataInfo.reversedFile = true;
        return importDataInfo;
    }

    public int getLoadedRows() {
        return this.loadedRows;
    }

    protected void parseTickData(Object[] objectArray) throws Exception {
        this.tickData.reset();
        block11: for (int i = 0; i < this.importInfo.columnTypes.size(); ++i) {
            DefaultCol defaultCol = this.importInfo.columnTypes.get(i);
            switch (defaultCol.getDataType()) {
                case 2: {
                    this.tickData.ask = (Double)objectArray[i];
                    continue block11;
                }
                case 3: {
                    this.tickData.bid = (Double)objectArray[i];
                    continue block11;
                }
                case 4: {
                    this.tickData.open = (Double)objectArray[i];
                    continue block11;
                }
                case 5: {
                    this.tickData.high = (Double)objectArray[i];
                    continue block11;
                }
                case 6: {
                    this.tickData.low = (Double)objectArray[i];
                    continue block11;
                }
                case 7: {
                    this.tickData.close = (Double)objectArray[i];
                    continue block11;
                }
                case 1: {
                    this.tickData.volume += (double)((Double)objectArray[i]).intValue();
                    continue block11;
                }
                case 9: {
                    this.tickData.time = (Long)objectArray[i];
                    continue block11;
                }
                case 8: {
                    throw new Exception("Cannot have indicator value in data file!");
                }
            }
        }
    }

    @Override
    public boolean readData() throws Exception {
        String string;
        if (this.rows == 0 && this.importInfo.skipRows > 0) {
            for (int i = 0; i < this.importInfo.skipRows; ++i) {
                this.readLine();
            }
        }
        this.currentLine = string = this.reader.readLine();
        if (string == null || string.equals("")) {
            return false;
        }
        ++this.loadedRows;
        String[] stringArray = null;
        int n = this.importInfo.columnTypes.size();
        String[] stringArray2 = new String[n];
        try {
            stringArray = string.split(this.importInfo.separator);
            if (this.importInfo.skipCols > 0) {
                if (stringArray.length - this.importInfo.skipCols <= 0) {
                    throw new Exception("There are less columns than specified in Skip Columns parameter!");
                }
                if (stringArray.length - this.importInfo.skipCols < n) {
                    throw new Exception(String.format("There are not enough data columns in the file! Found: %d, Required: %d", stringArray.length - this.importInfo.skipCols, n));
                }
                stringArray2 = Arrays.copyOfRange(stringArray, this.importInfo.skipCols, stringArray.length);
            } else {
                stringArray2 = stringArray;
            }
            if (this.importInfo.isMT5TickImport() && (stringArray2 = this.importInfo.correctMT5TickData(stringArray2)) == null) {
                this.tickData.reset();
                return true;
            }
            Object[] objectArray = this.parseLine(stringArray2, this.importInfo);
            this.parseTickData(objectArray);
            if (this.isDataCorrect()) {
                this.computeAveragePriceValue();
            }
            if (this.tickData.volume == 0.0) {
                this.tickData.volume = 1.0;
            }
        }
        catch (Exception exception) {
            if (this.importInfo.errorHandling == 1) {
                Log.info(String.format("[loading_data] Skipping row %d, line: %s, reason: %s", this.loadedRows, string, exception.getMessage()));
                this.tickData.time = Long.MIN_VALUE;
            }
            throw new Exception(String.format("Error parsing on line: %d, message: %s", this.loadedRows, exception.getMessage()));
        }
        return true;
    }

    @Override
    public void openFile() throws Exception {
        super.openFile();
        this.averagePriceValue = 0.0;
        this.previousTime = 0L;
    }

    private void computeAveragePriceValue() {
        double d = 0.0;
        int n = 0;
        if (this.tickData.ask != 0.0) {
            d += this.tickData.ask;
            ++n;
        }
        if (this.tickData.bid != 0.0) {
            d += this.tickData.bid;
            ++n;
        }
        if (this.tickData.open != 0.0) {
            d += this.tickData.open;
            ++n;
        }
        if (this.tickData.high != 0.0) {
            d += this.tickData.high;
            ++n;
        }
        if (this.tickData.low != 0.0) {
            d += this.tickData.low;
            ++n;
        }
        if (this.tickData.close != 0.0) {
            d += this.tickData.close;
            ++n;
        }
        this.averagePriceValue = d / (double)n;
    }

    public boolean isDataCorrect() {
        if (this.tickData.time == Long.MIN_VALUE) {
            return false;
        }
        if (this.averagePriceValue <= 0.0 || this.tickData.open < 0.0 || this.tickData.high < 0.0 || this.tickData.low < 0.0 || this.tickData.close < 0.0) {
            return true;
        }
        if (this.tickData.ask > 0.0 && (this.tickData.ask < this.averagePriceValue / 50.0 || this.tickData.ask > 50.0 * this.averagePriceValue)) {
            return false;
        }
        if (this.tickData.bid > 0.0 && (this.tickData.bid < this.averagePriceValue / 50.0 || this.tickData.bid > 50.0 * this.averagePriceValue)) {
            return false;
        }
        if (this.tickData.open > 0.0 && (this.tickData.open < this.averagePriceValue / 50.0 || this.tickData.open > 50.0 * this.averagePriceValue)) {
            return false;
        }
        if (this.tickData.high > 0.0 && (this.tickData.high < this.averagePriceValue / 50.0 || this.tickData.high > 50.0 * this.averagePriceValue)) {
            return false;
        }
        if (this.tickData.low > 0.0 && (this.tickData.low < this.averagePriceValue / 50.0 || this.tickData.low > 50.0 * this.averagePriceValue)) {
            return false;
        }
        return !(this.tickData.close > 0.0) || !(this.tickData.close < this.averagePriceValue / 50.0) && !(this.tickData.close > 50.0 * this.averagePriceValue);
    }

    public int getIndicatorsCount() {
        return 0;
    }

    public static void reset() {
    }

    public String getCurrentLine() {
        return this.currentLine;
    }

    public double getAveragePriceValue() {
        return this.averagePriceValue;
    }
}

