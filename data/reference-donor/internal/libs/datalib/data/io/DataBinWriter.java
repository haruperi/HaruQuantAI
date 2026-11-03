/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.data.io;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.io.ImportDataInfo;
import com.strategyquant.datalib.data.io.OhlcDataBinWriter;
import com.strategyquant.datalib.data.io.TickDataBinWriter;
import com.strategyquant.datalib.data.io.VersatileData;
import java.io.BufferedOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import javax.swing.JProgressBar;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class DataBinWriter {
    public static final Logger Log = LoggerFactory.getLogger((String)"DataBinWriter");
    private ImportDataInfo importInfo;
    private JProgressBar progressBar;
    private InstrumentInfo symbolInfo;
    private String fileName;
    protected DataOutputStream writer = null;
    private String dataPath = "";

    public DataBinWriter(String string) {
        this.dataPath = string;
    }

    public void setParams(ImportDataInfo importDataInfo, InstrumentInfo instrumentInfo, JProgressBar jProgressBar) {
        this.importInfo = importDataInfo;
        this.progressBar = jProgressBar;
        this.symbolInfo = instrumentInfo;
    }

    public void setFileName(String string) {
        this.fileName = string;
    }

    public void open() throws Exception {
        try {
            File file = new File(this.fileName);
            if (!file.exists()) {
                file.getParentFile().mkdirs();
            }
            this.writer = new DataOutputStream(new BufferedOutputStream(new FileOutputStream(this.fileName)));
            this.writeHeader();
        }
        catch (FileNotFoundException fileNotFoundException) {
            throw new Exception("File not found: " + this.fileName);
        }
    }

    public void close() throws Exception {
        try {
            this.writer.close();
            this.writer.flush();
            this.writer = null;
        }
        catch (IOException iOException) {
            throw new Exception("Cannot close file");
        }
    }

    public static DataBinWriter getInstance(int n, String string, InstrumentInfo instrumentInfo) {
        if (n == 2) {
            return new TickDataBinWriter(string);
        }
        return new OhlcDataBinWriter(string);
    }

    public void renameTempFile(String string) throws Exception {
        String string2 = this.dataPath + "temp/temp.dat";
        File file = new File(string2);
        if (!file.exists()) {
            throw new Exception("Temp file 'temp.dat' doesn't exist, nothing to rename!");
        }
        File file2 = new File(string);
        if (file2.exists() && !file2.delete()) {
            throw new Exception("Old data file '" + string + "' already exists and cannot be deleted, cannot import data!");
        }
        if (!file.renameTo(file2)) {
            throw new Exception("File cannot be renamed, cannot merge data!");
        }
        Log.info("Data file renamed to " + string);
    }

    protected abstract void writeHeader() throws Exception;

    public abstract void writeData(VersatileData var1) throws Exception;

    public abstract int getColumnsCount();
}

