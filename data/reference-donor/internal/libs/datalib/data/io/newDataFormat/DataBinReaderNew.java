/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.io.ImportDataInfo;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataManipulatorNew;
import com.strategyquant.datalib.data.io.newDataFormat.IRandomAccessReader;
import com.strategyquant.datalib.data.io.newDataFormat.OhlcDataBinReaderNew;
import com.strategyquant.datalib.data.io.newDataFormat.RandomAccessReaderArray;
import com.strategyquant.datalib.data.io.newDataFormat.RandomAccessReaderFile;
import com.strategyquant.datalib.data.io.newDataFormat.TickDataBinReaderNew;
import java.io.IOException;
import javax.swing.JProgressBar;

public abstract class DataBinReaderNew
extends DataManipulatorNew {
    protected ImportDataInfo importInfo;
    protected JProgressBar progressBar;
    protected DataInfo dataInfo;
    protected String fileName;
    protected IRandomAccessReader reader = null;
    public final VersatileData tickData = new VersatileData();
    private byte[] modificators;
    private int timeModificator;

    public static DataBinReaderNew getInstance(int n, InstrumentInfo instrumentInfo) {
        DataBinReaderNew dataBinReaderNew = null;
        dataBinReaderNew = n == 2 ? new TickDataBinReaderNew() : new OhlcDataBinReaderNew();
        DataBinReaderNew.setDecimals(instrumentInfo, dataBinReaderNew);
        return dataBinReaderNew;
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
        this.reader = new RandomAccessReaderFile(this.fileName);
        ((RandomAccessReaderFile)this.reader).openFile();
        this.readHeader();
    }

    public void setData(byte[] byArray) throws Exception {
        this.reader = new RandomAccessReaderArray(byArray);
        this.readHeader();
    }

    protected int readModificators() throws Exception {
        if (this.isCrypted()) {
            int n = this.reader.readInt();
            byte[] byArray = new byte[n];
            this.reader.readBytes(byArray);
            this.modificators = this.decryptModificators(byArray);
            this.timeModificator = this.modificators[0] + this.modificators[1] + this.modificators[2] + this.modificators[3];
            return 4 + n;
        }
        return 0;
    }

    protected void fixData(VersatileData versatileData, boolean bl) {
        if (!this.isCrypted()) {
            return;
        }
        if (bl) {
            versatileData.ask -= (double)this.modificators[0];
            versatileData.bid -= (double)this.modificators[1];
        } else {
            versatileData.open -= (double)this.modificators[0];
            versatileData.high -= (double)this.modificators[1];
            versatileData.low -= (double)this.modificators[2];
            versatileData.close -= (double)this.modificators[3];
        }
        versatileData.time -= (long)this.timeModificator;
        versatileData.volume -= (double)this.modificators[0];
    }

    public void closeFile() throws Exception {
        try {
            if (this.reader instanceof RandomAccessReaderFile) {
                ((RandomAccessReaderFile)this.reader).closeFile();
            }
        }
        catch (IOException iOException) {
            throw new Exception("Cannot close file");
        }
    }

    public boolean isDataCorrect() {
        return true;
    }

    public boolean dataRemaining() {
        return this.reader.dataRemaining();
    }

    public abstract void readHeader() throws Exception;

    public abstract int getColumnsCount();

    public abstract boolean readData() throws Exception;

    public abstract void seek(int var1) throws Exception;

    public abstract long getTotalRecords() throws Exception;
}

