/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io;

import com.strategyquant.datalib.data.io.DataBinReader;
import com.strategyquant.datalib.data.io.FileChannelReader;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.channels.FileChannel;

public class TickDataBinReader
extends DataBinReader {
    private FileChannel inChannel;
    private FileChannelReader reader;
    private long totalRecords = 0L;
    private long currentRecord = 0L;

    @Override
    public void openFile() throws Exception {
        try {
            this.inChannel = new FileInputStream(this.fileName).getChannel();
            this.reader = new FileChannelReader(this.inChannel, 64);
            this.totalRecords = this.inChannel.size() / (long)FileChannelReader.getDataSize();
            this.currentRecord = 0L;
        }
        catch (FileNotFoundException fileNotFoundException) {
            throw new Exception("File not found: " + this.fileName);
        }
        catch (IOException iOException) {
            throw new Exception("IO Exception: " + iOException.getMessage());
        }
    }

    @Override
    public void closeFile() throws Exception {
        this.inChannel.close();
    }

    @Override
    public int getColumnsCount() {
        return 0;
    }

    @Override
    public boolean readData() throws Exception {
        this.tickData.reset();
        if (this.currentRecord == this.totalRecords) {
            return false;
        }
        try {
            this.reader.getData(this.tickData);
            return true;
        }
        catch (IOException iOException) {
            return false;
        }
    }

    @Override
    public void readHeader() throws Exception {
    }
}

