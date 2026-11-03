/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.IRandomAccessReader;
import com.strategyquant.datalib.data.io.newDataFormat.NewDataFormatReader;
import java.io.EOFException;

public class TickDataReader
extends NewDataFormatReader {
    private long prevTime;
    private long prevAsk;
    private long prevBid;
    private long prevVolume;
    private byte[] configBytes = new byte[2];

    public TickDataReader() {
        this(false);
    }

    public TickDataReader(boolean bl) {
        super(bl);
    }

    @Override
    protected int getMinimalRecordSize() {
        return 6;
    }

    @Override
    protected int getMaximalRecordSize() {
        return 34;
    }

    @Override
    protected void readAndTrashNRecords(long l, IRandomAccessReader iRandomAccessReader) throws Exception {
        VersatileData versatileData = new VersatileData();
        int n = 0;
        while ((long)n < l) {
            this.readData(iRandomAccessReader, versatileData);
            ++n;
        }
    }

    public void readData(IRandomAccessReader iRandomAccessReader, VersatileData versatileData) throws Exception {
        if (!iRandomAccessReader.dataRemaining()) {
            throw new EOFException();
        }
        if (this.start) {
            if (this.isForceOldFormat()) {
                this.setNewFormat(false);
            } else {
                this.checkFormat(iRandomAccessReader);
            }
        }
        if (this.isNewFormat() && this.shouldLoadStartChain()) {
            this.readMagicChain(iRandomAccessReader, false);
        }
        iRandomAccessReader.readBytes(this.configBytes);
        this.start = true;
        int n = this.getBitValue(this.configBytes, 1);
        int n2 = this.getBitValue(this.configBytes, 1);
        int n3 = this.getBitValue(this.configBytes, 1);
        int n4 = this.getBitValue(this.configBytes, 1);
        this.start = true;
        int n5 = this.getBitValue(this.configBytes, 0);
        int n6 = this.getBitValue(this.configBytes, 0);
        int n7 = this.getBitValue(this.configBytes, 0);
        int n8 = this.getBitValue(this.configBytes, 0);
        versatileData.time = this.getTime(iRandomAccessReader, n7, n8);
        versatileData.ask = this.getAsk(iRandomAccessReader, n5, n6);
        versatileData.bid = this.getBid(iRandomAccessReader, n3, n4);
        versatileData.volume = this.getVolume(iRandomAccessReader, n, n2);
        this.nextLoaded();
    }

    private long getTime(IRandomAccessReader iRandomAccessReader, int n, int n2) throws Exception {
        long l = this.getValue(iRandomAccessReader, n);
        switch (n2) {
            case 0: {
                this.prevTime -= l;
                return this.prevTime;
            }
            case 1: {
                this.prevTime += l;
                return this.prevTime;
            }
            case 2: {
                this.prevTime = l;
                return l;
            }
        }
        throw new Exception("Unknown logic type of value " + n2);
    }

    private double getAsk(IRandomAccessReader iRandomAccessReader, int n, int n2) throws Exception {
        long l = this.getValue(iRandomAccessReader, n);
        switch (n2) {
            case 0: {
                this.prevAsk -= l;
                return (double)this.prevAsk / this.decimalsConstant;
            }
            case 1: {
                this.prevAsk += l;
                return (double)this.prevAsk / this.decimalsConstant;
            }
            case 2: {
                this.prevAsk = l;
                return (double)l / this.decimalsConstant;
            }
        }
        throw new Exception("Unknown logic type of value " + n2);
    }

    private double getBid(IRandomAccessReader iRandomAccessReader, int n, int n2) throws Exception {
        long l = this.getValue(iRandomAccessReader, n);
        switch (n2) {
            case 0: {
                this.prevBid -= l;
                return (double)this.prevBid / this.decimalsConstant;
            }
            case 1: {
                this.prevBid += l;
                return (double)this.prevBid / this.decimalsConstant;
            }
            case 2: {
                this.prevBid = l;
                return (double)l / this.decimalsConstant;
            }
        }
        throw new Exception("Unknown logic type of value " + n2);
    }

    private double getVolume(IRandomAccessReader iRandomAccessReader, int n, int n2) throws Exception {
        long l = this.getValue(iRandomAccessReader, n);
        switch (n2) {
            case 0: {
                this.prevVolume -= l;
                return (double)this.prevVolume / this.volumeConstant;
            }
            case 1: {
                this.prevVolume += l;
                return (double)this.prevVolume / this.volumeConstant;
            }
            case 2: {
                this.prevVolume = l;
                return (double)l / this.volumeConstant;
            }
        }
        throw new Exception("Unknown logic type of value " + n2);
    }
}

