/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.io.ImportDataInfo;
import com.strategyquant.datalib.data.io.OhlcDataBinReader;
import com.strategyquant.datalib.data.io.TickDataBinReader;
import com.strategyquant.datalib.data.io.VersatileData;
import java.io.BufferedInputStream;
import java.io.DataInputStream;
import java.io.FileInputStream;
import java.io.IOException;
import javax.swing.JProgressBar;

public abstract class DataBinReader {
    protected ImportDataInfo importInfo;
    protected JProgressBar progressBar;
    protected DataInfo dataInfo;
    protected String fileName;
    protected DataInputStream reader = null;
    public final VersatileData tickData = new VersatileData();

    public static DataBinReader getInstance(int n, int n2) {
        if (n == 2) {
            return new TickDataBinReader();
        }
        return new OhlcDataBinReader();
    }

    public void setParams(ImportDataInfo importDataInfo, DataInfo dataInfo, JProgressBar jProgressBar) {
        this.importInfo = importDataInfo;
        this.progressBar = jProgressBar;
        this.dataInfo = dataInfo;
    }

    public void setFileName(String string) {
        this.fileName = string;
    }

    public void openFile() throws Exception {
        this.reader = new DataInputStream(new BufferedInputStream(new FileInputStream(this.fileName)));
        this.readHeader();
    }

    public void closeFile() throws Exception {
        try {
            this.reader.close();
        }
        catch (IOException iOException) {
            throw new Exception("Cannot close file");
        }
    }

    public boolean isDataCorrect() {
        return true;
    }

    public abstract void readHeader() throws Exception;

    public abstract int getColumnsCount();

    public abstract boolean readData() throws Exception;
}

