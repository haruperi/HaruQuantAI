/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.utils.IProgressListener
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.data.io;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.io.ImportDataInfo;
import com.strategyquant.datalib.data.io.TimeframeRecognizer;
import com.strategyquant.datalib.data.io.columns.DefaultCol;
import com.strategyquant.lib.utils.IProgressListener;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import javax.swing.JProgressBar;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class AbstractDataCsvLoader {
    public static final Logger Log = LoggerFactory.getLogger(AbstractDataCsvLoader.class);
    public static final String InvalidTimeConsecution = "Invalid time consecution. Each row must have same or latter time than the previous one";
    protected ImportDataInfo importInfo;
    protected JProgressBar progressBar;
    protected DataInfo dataInfo;
    protected String fileName;
    protected SimpleDateFormat df = null;
    protected int timeColumn = 0;
    protected boolean isTimeCol;
    protected volatile boolean cancel = false;
    protected volatile boolean paused = false;
    protected IProgressListener listener;
    protected BufferedReader reader = null;
    protected int rows;
    public int loadedRows;
    protected TimeframeRecognizer tfRecognizer = new TimeframeRecognizer();
    protected long previousTime;
    protected double progressPercent = 0.0;

    public abstract boolean readData() throws Exception;

    public Object[] parseLine(String[] stringArray, ImportDataInfo importDataInfo) throws Exception {
        int n;
        Object[] objectArray = new Object[stringArray.length];
        for (n = 0; n < objectArray.length; ++n) {
            objectArray[n] = null;
        }
        if (stringArray.length != importDataInfo.columnTypes.size()) {
            throw new Exception("The number of columns in data file doesn't match!(CSV columns: " + stringArray.length + ", ImportDataInfo columns: " + importDataInfo.columnTypes.size());
        }
        block10: for (n = 0; n < importDataInfo.columnTypes.size(); ++n) {
            DefaultCol defaultCol = importDataInfo.columnTypes.get(n);
            switch (defaultCol.getType()) {
                case 1: {
                    objectArray[n] = Integer.parseInt(stringArray[n]);
                    continue block10;
                }
                case 2: {
                    objectArray[n] = Long.parseLong(stringArray[n]);
                    continue block10;
                }
                case 4: {
                    objectArray[n] = stringArray[n];
                    continue block10;
                }
                case 5: {
                    objectArray[n] = AbstractDataCsvLoader.parseDoubleSpecial(stringArray[n]);
                    continue block10;
                }
                case 9: {
                    objectArray[n] = AbstractDataCsvLoader.parseDoubleSpecial(stringArray[n]);
                    continue block10;
                }
                case 6: {
                    objectArray[n] = this.parseTime(stringArray[n], stringArray, importDataInfo);
                    continue block10;
                }
                case 10: {
                    objectArray[n] = this.parseTime(stringArray[n], stringArray, importDataInfo);
                    continue block10;
                }
            }
        }
        return objectArray;
    }

    public static int intValueOf(String string) {
        char c;
        int n;
        boolean bl;
        int n2;
        int n3;
        block7: {
            block6: {
                n3 = 0;
                n2 = 0;
                bl = false;
                if (string == null || (n = string.length()) == 0) break block6;
                c = string.charAt(0);
                if (c >= '0' && c <= '9') break block7;
                boolean bl2 = bl = c == '-';
                if (bl2 && ++n2 != n && (c = string.charAt(n2)) >= '0' && c <= '9') break block7;
            }
            throw new NumberFormatException(string);
        }
        while (true) {
            n3 += 48 - c;
            if (++n2 == n) {
                return bl ? n3 : -n3;
            }
            c = string.charAt(n2);
            if (c < '0' || c > '9') {
                throw new NumberFormatException(string);
            }
            n3 *= 10;
        }
    }

    private static double parseDoubleSpecial(String string) throws Exception {
        Exception exception = null;
        try {
            return Double.parseDouble(string);
        }
        catch (Exception exception2) {
            exception = exception2;
            try {
                return Double.parseDouble(string.replace(",", "."));
            }
            catch (Exception exception3) {
                exception = exception3;
                throw exception;
            }
        }
    }

    private long parseTime(String string, String[] stringArray, ImportDataInfo importDataInfo) throws Exception {
        if (importDataInfo.dateFormat.equals("Long (millis from epoch)") || importDataInfo.dateFormat.equals("Long (seconds from epoch)")) {
            return this.parseLongTime(string, importDataInfo.dateFormat);
        }
        try {
            if (this.df == null) {
                this.initializeDateFormat(importDataInfo);
            }
            if (this.isTimeCol) {
                string = string + " " + stringArray[this.timeColumn];
            }
            Date date = this.df.parse(string);
            return date.getTime();
        }
        catch (Exception exception) {
            throw new Exception("Parsing DateTime failed! Date: " + string + ", Expected format: " + this.df.toPattern() + ", ImportDataInfo format: " + importDataInfo.dateFormat, exception);
        }
    }

    private long parseLongTime(String string, String string2) throws Exception {
        try {
            long l = Long.parseLong(string);
            return string2.equals("Long (seconds from epoch)") ? l * 1000L : l;
        }
        catch (Exception exception) {
            throw new Exception("Parsing DateTime failed! Date: " + string + " - Incorrect value for Long format", exception);
        }
    }

    private void initializeDateFormat(ImportDataInfo importDataInfo) {
        Object object;
        this.df = new SimpleDateFormat();
        int n = 0;
        this.isTimeCol = false;
        for (n = 0; n < importDataInfo.columnTypes.size(); ++n) {
            object = importDataInfo.columnTypes.get(n);
            if (((DefaultCol)object).getType() != 7) continue;
            this.isTimeCol = true;
            break;
        }
        this.timeColumn = n;
        if (this.isTimeCol) {
            object = importDataInfo.dateFormat;
            if (!((String)object).contains("HH")) {
                String string = importDataInfo.timeFormat;
                object = string == null ? (String)object + " HH:mm" : (String)object + " " + string;
            }
            this.df.applyPattern((String)object);
        } else {
            importDataInfo.dateFormat = importDataInfo.dateFormat.replaceAll("hh", "HH");
            this.df.applyPattern(importDataInfo.dateFormat);
        }
    }

    public int countRows(String string) {
        try {
            BufferedReader bufferedReader = new BufferedReader(new FileReader(new File(string)));
            String string2 = null;
            int n = 0;
            while (true) {
                try {
                    string2 = bufferedReader.readLine();
                }
                catch (IOException iOException) {
                    Log.error("Exception", (Throwable)iOException);
                }
                if (string2 == null) break;
                ++n;
            }
            bufferedReader.close();
            return n;
        }
        catch (IOException iOException) {
            Log.error("Exception", (Throwable)iOException);
            return -1;
        }
    }

    public void openFile() throws Exception {
        try {
            this.reader = new BufferedReader(new FileReader(new File(this.importInfo.filePath)));
            this.rows = 0;
            this.tfRecognizer.reset();
        }
        catch (FileNotFoundException fileNotFoundException) {
            throw new Exception("File not found: " + this.importInfo.filePath);
        }
    }

    public void close() throws Exception {
        if (this.reader != null) {
            try {
                this.reader.close();
                this.reader = null;
            }
            catch (IOException iOException) {
                throw new Exception("Cannot close file");
            }
        }
    }

    protected String readLine() throws Exception {
        try {
            ++this.rows;
            String string = this.reader.readLine();
            if (string != null && string.equalsIgnoreCase("")) {
                string = this.reader.readLine();
            }
            if (string != null && string.equalsIgnoreCase("")) {
                string = this.reader.readLine();
            }
            return string;
        }
        catch (IOException iOException) {
            throw new Exception(String.format("Cannot read lines at line: %d", this.rows));
        }
    }

    public void cancel() {
        this.cancel = true;
    }

    public String recognizeTimeframe() {
        return this.tfRecognizer.getTimeframe();
    }

    public void pause() {
        this.paused = true;
    }

    public void restart() {
        this.paused = false;
    }

    protected void checkPaused() throws InterruptedException {
        if (!this.paused) {
            return;
        }
        this.listener.onPause();
        while (this.paused && !this.cancel) {
            Thread.sleep(100L);
        }
        this.listener.onContinue();
    }
}

