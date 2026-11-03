/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.NewDataFormatWritter;
import com.strategyquant.datalib.data.io.newDataFormat.RandomAccessReaderOffheap;
import java.io.DataOutputStream;
import java.nio.ByteBuffer;

public class OhlcDataWriter
extends NewDataFormatWritter {
    private long prevTime;
    private long prevOpen;
    private long prevHigh;
    private long prevLow;
    private long prevClose;
    private long prevVolume;

    public OhlcDataWriter() {
        this(false);
    }

    public OhlcDataWriter(boolean bl) {
        super(bl);
    }

    public void writeData(DataOutputStream dataOutputStream, VersatileData versatileData) throws Exception {
        long l = Math.round(versatileData.open * this.decimalsConstant);
        long l2 = Math.round(versatileData.high * this.decimalsConstant);
        long l3 = Math.round(versatileData.low * this.decimalsConstant);
        long l4 = Math.round(versatileData.close * this.decimalsConstant);
        long l5 = Math.round(versatileData.volume * this.volumeConstant);
        if (l5 < 0L) {
            l5 = Long.MAX_VALUE;
        }
        if (this.shouldWriteFullData()) {
            this.start = false;
            if (!this.isForceOldFormat()) {
                this.writeMagicChain(dataOutputStream);
            }
            int[] nArray = new int[]{2, 2, 2, 2, 2, 2};
            int[] nArray2 = new int[]{3, 3, 3, 3, 3, 3};
            dataOutputStream.write(this.getConfigBytes(nArray, nArray2));
            dataOutputStream.writeLong(versatileData.time);
            dataOutputStream.writeLong(l);
            dataOutputStream.writeLong(l2);
            dataOutputStream.writeLong(l3);
            dataOutputStream.writeLong(l4);
            dataOutputStream.writeLong(l5);
        } else {
            long l6 = versatileData.time - this.prevTime;
            long l7 = l - this.prevOpen;
            long l8 = l2 - this.prevHigh;
            long l9 = l3 - this.prevLow;
            long l10 = l4 - this.prevClose;
            long l11 = l5 - this.prevVolume;
            int[] nArray = new int[]{OhlcDataWriter.getLogicType(l6), OhlcDataWriter.getLogicType(l7), OhlcDataWriter.getLogicType(l8), OhlcDataWriter.getLogicType(l9), OhlcDataWriter.getLogicType(l10), OhlcDataWriter.getLogicType(l11)};
            int[] nArray3 = new int[]{OhlcDataWriter.getDataType(l6), OhlcDataWriter.getDataType(l7), OhlcDataWriter.getDataType(l8), OhlcDataWriter.getDataType(l9), OhlcDataWriter.getDataType(l10), OhlcDataWriter.getDataType(l11)};
            dataOutputStream.write(this.getConfigBytes(nArray, nArray3));
            this.writeValue(dataOutputStream, l6, nArray3[0]);
            this.writeValue(dataOutputStream, l7, nArray3[1]);
            this.writeValue(dataOutputStream, l8, nArray3[2]);
            this.writeValue(dataOutputStream, l9, nArray3[3]);
            this.writeValue(dataOutputStream, l10, nArray3[4]);
            this.writeValue(dataOutputStream, l11, nArray3[5]);
        }
        this.prevTime = versatileData.time;
        this.prevOpen = l;
        this.prevHigh = l2;
        this.prevLow = l3;
        this.prevClose = l4;
        this.prevVolume = l5;
        this.nextSaved();
    }

    public void putData(ByteBuffer byteBuffer, VersatileData versatileData) throws Exception {
        long l = Math.round(versatileData.open * this.decimalsConstant);
        long l2 = Math.round(versatileData.high * this.decimalsConstant);
        long l3 = Math.round(versatileData.low * this.decimalsConstant);
        long l4 = Math.round(versatileData.close * this.decimalsConstant);
        long l5 = Math.round(versatileData.volume * this.volumeConstant);
        if (this.shouldWriteFullData()) {
            this.start = false;
            if (!this.isForceOldFormat()) {
                this.writeMagicChain(byteBuffer);
            }
            int[] nArray = new int[]{2, 2, 2, 2, 2, 2};
            int[] nArray2 = new int[]{3, 3, 3, 3, 3, 3};
            byteBuffer.put(this.getConfigBytes(nArray, nArray2));
            byteBuffer.putLong(versatileData.time);
            byteBuffer.putLong(l);
            byteBuffer.putLong(l2);
            byteBuffer.putLong(l3);
            byteBuffer.putLong(l4);
            byteBuffer.putLong(l5);
        } else {
            long l6 = versatileData.time - this.prevTime;
            long l7 = l - this.prevOpen;
            long l8 = l2 - this.prevHigh;
            long l9 = l3 - this.prevLow;
            long l10 = l4 - this.prevClose;
            long l11 = l5 - this.prevVolume;
            int[] nArray = new int[]{OhlcDataWriter.getLogicType(l6), OhlcDataWriter.getLogicType(l7), OhlcDataWriter.getLogicType(l8), OhlcDataWriter.getLogicType(l9), OhlcDataWriter.getLogicType(l10), OhlcDataWriter.getLogicType(l11)};
            int[] nArray3 = new int[]{OhlcDataWriter.getDataType(l6), OhlcDataWriter.getDataType(l7), OhlcDataWriter.getDataType(l8), OhlcDataWriter.getDataType(l9), OhlcDataWriter.getDataType(l10), OhlcDataWriter.getDataType(l11)};
            byteBuffer.put(this.getConfigBytes(nArray, nArray3));
            this.putValue(byteBuffer, l6, nArray3[0]);
            this.putValue(byteBuffer, l7, nArray3[1]);
            this.putValue(byteBuffer, l8, nArray3[2]);
            this.putValue(byteBuffer, l9, nArray3[3]);
            this.putValue(byteBuffer, l10, nArray3[4]);
            this.putValue(byteBuffer, l11, nArray3[5]);
        }
        this.prevTime = versatileData.time;
        this.prevOpen = l;
        this.prevHigh = l2;
        this.prevLow = l3;
        this.prevClose = l4;
        this.prevVolume = l5;
        this.nextSaved();
    }

    public void putData(RandomAccessReaderOffheap randomAccessReaderOffheap, VersatileData versatileData) throws Exception {
        long l = Math.round(versatileData.open * this.decimalsConstant);
        long l2 = Math.round(versatileData.high * this.decimalsConstant);
        long l3 = Math.round(versatileData.low * this.decimalsConstant);
        long l4 = Math.round(versatileData.close * this.decimalsConstant);
        long l5 = Math.round(versatileData.volume * this.volumeConstant);
        if (this.shouldWriteFullData()) {
            this.start = false;
            if (!this.isForceOldFormat()) {
                this.writeMagicChain(randomAccessReaderOffheap);
            }
            int[] nArray = new int[]{2, 2, 2, 2, 2, 2};
            int[] nArray2 = new int[]{3, 3, 3, 3, 3, 3};
            randomAccessReaderOffheap.put(this.getConfigBytes(nArray, nArray2));
            randomAccessReaderOffheap.putLong(versatileData.time);
            randomAccessReaderOffheap.putLong(l);
            randomAccessReaderOffheap.putLong(l2);
            randomAccessReaderOffheap.putLong(l3);
            randomAccessReaderOffheap.putLong(l4);
            randomAccessReaderOffheap.putLong(l5);
        } else {
            long l6 = versatileData.time - this.prevTime;
            long l7 = l - this.prevOpen;
            long l8 = l2 - this.prevHigh;
            long l9 = l3 - this.prevLow;
            long l10 = l4 - this.prevClose;
            long l11 = l5 - this.prevVolume;
            int[] nArray = new int[]{OhlcDataWriter.getLogicType(l6), OhlcDataWriter.getLogicType(l7), OhlcDataWriter.getLogicType(l8), OhlcDataWriter.getLogicType(l9), OhlcDataWriter.getLogicType(l10), OhlcDataWriter.getLogicType(l11)};
            int[] nArray3 = new int[]{OhlcDataWriter.getDataType(l6), OhlcDataWriter.getDataType(l7), OhlcDataWriter.getDataType(l8), OhlcDataWriter.getDataType(l9), OhlcDataWriter.getDataType(l10), OhlcDataWriter.getDataType(l11)};
            randomAccessReaderOffheap.put(this.getConfigBytes(nArray, nArray3));
            this.putValue(randomAccessReaderOffheap, l6, nArray3[0]);
            this.putValue(randomAccessReaderOffheap, l7, nArray3[1]);
            this.putValue(randomAccessReaderOffheap, l8, nArray3[2]);
            this.putValue(randomAccessReaderOffheap, l9, nArray3[3]);
            this.putValue(randomAccessReaderOffheap, l10, nArray3[4]);
            this.putValue(randomAccessReaderOffheap, l11, nArray3[5]);
        }
        this.prevTime = versatileData.time;
        this.prevOpen = l;
        this.prevHigh = l2;
        this.prevLow = l3;
        this.prevClose = l4;
        this.prevVolume = l5;
        this.nextSaved();
    }

    private void putValue(RandomAccessReaderOffheap randomAccessReaderOffheap, long l, int n) throws Exception {
        if (l < 0L) {
            l = -l;
        }
        switch (n) {
            case 0: {
                randomAccessReaderOffheap.put((byte)l);
                break;
            }
            case 1: {
                randomAccessReaderOffheap.putShort((short)l);
                break;
            }
            case 2: {
                randomAccessReaderOffheap.putInt((int)l);
                break;
            }
            case 3: {
                randomAccessReaderOffheap.putLong(l);
                break;
            }
            default: {
                throw new Exception("Invalid data type of value " + n);
            }
        }
    }

    private void putValue(ByteBuffer byteBuffer, long l, int n) throws Exception {
        if (l < 0L) {
            l = -l;
        }
        switch (n) {
            case 0: {
                byteBuffer.put((byte)l);
                break;
            }
            case 1: {
                byteBuffer.putShort((short)l);
                break;
            }
            case 2: {
                byteBuffer.putInt((int)l);
                break;
            }
            case 3: {
                byteBuffer.putLong(l);
                break;
            }
            default: {
                throw new Exception("Invalid data type of value " + n);
            }
        }
    }
}

