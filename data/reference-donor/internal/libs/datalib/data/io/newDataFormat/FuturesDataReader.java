/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.FuturesVersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.IRandomAccessReader;
import com.strategyquant.datalib.data.io.newDataFormat.NewDataFormatReader;
import java.io.EOFException;

public class FuturesDataReader
extends NewDataFormatReader {
    private long prevTime;
    private long prevOpen;
    private long prevHigh;
    private long prevLow;
    private long prevClose;
    private long prevVolume;
    private long prevOpenInterest;
    private byte[] configBytes = new byte[4];

    public FuturesDataReader() {
        this(false);
    }

    public FuturesDataReader(boolean bl) {
        super(bl);
    }

    @Override
    protected int getMinimalRecordSize() {
        return 7;
    }

    @Override
    protected int getMaximalRecordSize() {
        return 42;
    }

    @Override
    protected void readAndTrashNRecords(long l, IRandomAccessReader iRandomAccessReader) throws Exception {
        FuturesVersatileData futuresVersatileData = new FuturesVersatileData();
        int n = 0;
        while ((long)n < l) {
            this.readData(iRandomAccessReader, futuresVersatileData);
            ++n;
        }
    }

    public void readData(IRandomAccessReader iRandomAccessReader, FuturesVersatileData futuresVersatileData) throws Exception {
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
        int n = this.getBitValue(this.configBytes, 3);
        int n2 = this.getBitValue(this.configBytes, 3);
        int n3 = this.getBitValue(this.configBytes, 3);
        int n4 = this.getBitValue(this.configBytes, 3);
        this.start = true;
        int n5 = this.getBitValue(this.configBytes, 2);
        int n6 = this.getBitValue(this.configBytes, 2);
        int n7 = this.getBitValue(this.configBytes, 2);
        int n8 = this.getBitValue(this.configBytes, 2);
        this.start = true;
        int n9 = this.getBitValue(this.configBytes, 1);
        int n10 = this.getBitValue(this.configBytes, 1);
        int n11 = this.getBitValue(this.configBytes, 1);
        int n12 = this.getBitValue(this.configBytes, 1);
        this.start = true;
        int n13 = this.getBitValue(this.configBytes, 0);
        int n14 = this.getBitValue(this.configBytes, 0);
        int n15 = this.getBitValue(this.configBytes, 0);
        int n16 = this.getBitValue(this.configBytes, 0);
        futuresVersatileData.time = this.getTime(iRandomAccessReader, n15, n16);
        futuresVersatileData.open = this.getOpen(iRandomAccessReader, n13, n14);
        futuresVersatileData.high = this.getHigh(iRandomAccessReader, n11, n12);
        futuresVersatileData.low = this.getLow(iRandomAccessReader, n9, n10);
        futuresVersatileData.close = this.getClose(iRandomAccessReader, n7, n8);
        futuresVersatileData.volume = this.getVolume(iRandomAccessReader, n5, n6);
        futuresVersatileData.openInterest = this.getOpenInterest(iRandomAccessReader, n3, n4);
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

    private double getOpen(IRandomAccessReader iRandomAccessReader, int n, int n2) throws Exception {
        long l = this.getValue(iRandomAccessReader, n);
        switch (n2) {
            case 0: {
                this.prevOpen -= l;
                return (double)this.prevOpen / this.decimalsConstant;
            }
            case 1: {
                this.prevOpen += l;
                return (double)this.prevOpen / this.decimalsConstant;
            }
            case 2: {
                this.prevOpen = l;
                return (double)l / this.decimalsConstant;
            }
        }
        throw new Exception("Unknown logic type of value " + n2);
    }

    private double getHigh(IRandomAccessReader iRandomAccessReader, int n, int n2) throws Exception {
        long l = this.getValue(iRandomAccessReader, n);
        switch (n2) {
            case 0: {
                this.prevHigh -= l;
                return (double)this.prevHigh / this.decimalsConstant;
            }
            case 1: {
                this.prevHigh += l;
                return (double)this.prevHigh / this.decimalsConstant;
            }
            case 2: {
                this.prevHigh = l;
                return (double)l / this.decimalsConstant;
            }
        }
        throw new Exception("Unknown logic type of value " + n2);
    }

    private double getLow(IRandomAccessReader iRandomAccessReader, int n, int n2) throws Exception {
        long l = this.getValue(iRandomAccessReader, n);
        switch (n2) {
            case 0: {
                this.prevLow -= l;
                return (double)this.prevLow / this.decimalsConstant;
            }
            case 1: {
                this.prevLow += l;
                return (double)this.prevLow / this.decimalsConstant;
            }
            case 2: {
                this.prevLow = l;
                return (double)l / this.decimalsConstant;
            }
        }
        throw new Exception("Unknown logic type of value " + n2);
    }

    private double getClose(IRandomAccessReader iRandomAccessReader, int n, int n2) throws Exception {
        long l = this.getValue(iRandomAccessReader, n);
        switch (n2) {
            case 0: {
                this.prevClose -= l;
                return (double)this.prevClose / this.decimalsConstant;
            }
            case 1: {
                this.prevClose += l;
                return (double)this.prevClose / this.decimalsConstant;
            }
            case 2: {
                this.prevClose = l;
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

    private double getOpenInterest(IRandomAccessReader iRandomAccessReader, int n, int n2) throws Exception {
        long l = this.getValue(iRandomAccessReader, n);
        switch (n2) {
            case 0: {
                this.prevOpenInterest -= l;
                return (double)this.prevOpenInterest / this.volumeConstant;
            }
            case 1: {
                this.prevOpenInterest += l;
                return (double)this.prevOpenInterest / this.volumeConstant;
            }
            case 2: {
                this.prevOpenInterest = l;
                return (double)l / this.volumeConstant;
            }
        }
        throw new Exception("Unknown logic type of value " + n2);
    }
}

