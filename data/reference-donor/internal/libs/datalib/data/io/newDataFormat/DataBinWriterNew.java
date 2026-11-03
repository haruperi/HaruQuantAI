/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataManipulatorNew;
import com.strategyquant.datalib.data.io.newDataFormat.OhlcDataBinWriterNew;
import com.strategyquant.datalib.data.io.newDataFormat.TickDataBinWriterNew;
import java.io.BufferedOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class DataBinWriterNew
extends DataManipulatorNew {
    public static final Logger Log = LoggerFactory.getLogger((String)"DataBinWriterNew");
    private String fileName;
    protected DataOutputStream writer = null;
    private String dataPath = "";
    protected byte[] modificators;
    private VersatileData modifiedVersatileData;
    protected int timeModificator;

    public DataBinWriterNew(String string) {
        this.dataPath = string;
    }

    protected void writeModificatorsToHeader() throws Exception {
        if (this.isCrypted()) {
            this.modificators = this.generateModificators();
            byte[] byArray = this.encryptModificators(this.modificators);
            this.writer.writeInt(byArray.length);
            this.writer.write(byArray);
            this.modifiedVersatileData = new VersatileData();
            this.timeModificator = this.modificators[0] + this.modificators[1] + this.modificators[2] + this.modificators[3];
        }
    }

    protected VersatileData modifyDataBeforeSave(VersatileData versatileData, boolean bl) {
        if (!this.isCrypted()) {
            return versatileData;
        }
        if (bl) {
            this.modifiedVersatileData.ask = versatileData.ask + (double)this.modificators[0];
            this.modifiedVersatileData.bid = versatileData.bid + (double)this.modificators[1];
        } else {
            this.modifiedVersatileData.open = versatileData.open + (double)this.modificators[0];
            this.modifiedVersatileData.high = versatileData.high + (double)this.modificators[1];
            this.modifiedVersatileData.low = versatileData.low + (double)this.modificators[2];
            this.modifiedVersatileData.close = versatileData.close + (double)this.modificators[3];
        }
        this.modifiedVersatileData.time = versatileData.time + (long)this.timeModificator;
        this.modifiedVersatileData.volume = versatileData.volume + (double)this.modificators[0];
        return this.modifiedVersatileData;
    }

    protected void writeHeader() throws Exception {
        this.writer.writeUTF("4.2");
        this.writer.writeUTF(this.isCrypted() ? "C" : "D");
        this.writer.writeUTF("ABCDEFGH");
        this.writer.writeLong(0L);
        this.writer.writeInt(this.getColumnsCount());
        for (int i = 0; i < this.getColumnsCount(); ++i) {
            this.writer.writeUTF("_");
            this.writer.writeInt(0);
        }
        this.writer.writeUTF("SnRbTs");
        this.writeModificatorsToHeader();
    }

    protected byte[] generateModificators() {
        return new byte[]{(byte)(Math.random() * 100.0), (byte)(Math.random() * 150.0), (byte)(Math.random() * 111.0), (byte)(Math.random() * 49.0)};
    }

    public static DataBinWriterNew getInstance(int n, String string, InstrumentInfo instrumentInfo) {
        DataBinWriterNew dataBinWriterNew = null;
        dataBinWriterNew = n == 2 ? new TickDataBinWriterNew(string) : new OhlcDataBinWriterNew(string);
        DataBinWriterNew.setDecimals(instrumentInfo, dataBinWriterNew);
        return dataBinWriterNew;
    }

    public static DataBinWriterNew getCryptedInstance(int n, String string, InstrumentInfo instrumentInfo) {
        DataBinWriterNew dataBinWriterNew = null;
        dataBinWriterNew = n == 2 ? new TickDataBinWriterNew(string) : new OhlcDataBinWriterNew(string);
        dataBinWriterNew.setCrypted(true);
        DataBinWriterNew.setDecimals(instrumentInfo, dataBinWriterNew);
        return dataBinWriterNew;
    }

    public void setFileName(String string) {
        this.fileName = string;
    }

    public String getFileName() {
        return this.fileName;
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
        if (this.writer != null) {
            try {
                this.writer.flush();
                this.writer.close();
                this.writer = null;
                this.reset();
            }
            catch (IOException iOException) {
                throw new Exception("Cannot close file");
            }
        }
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

    public abstract void writeData(VersatileData var1) throws Exception;

    public abstract int getColumnsCount();

    public abstract void reset();
}

