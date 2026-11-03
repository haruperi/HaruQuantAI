/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.NewDataFormatWritter;
import com.strategyquant.datalib.data.io.newDataFormat.RandomAccessReaderOffheap;
import java.io.DataOutputStream;
import java.nio.ByteBuffer;

public class TickDataWriter
extends NewDataFormatWritter {
    private long prevTime;
    private long prevAsk;
    private long prevBid;
    private long prevVolume;
    int[] logicTypes = new int[]{2, 2, 2, 2};
    int[] dataTypes = new int[]{3, 3, 3, 3};

    public TickDataWriter(boolean bl) {
        super(bl);
    }

    public TickDataWriter() {
        this(false);
    }

    public void writeData(DataOutputStream dataOutputStream, VersatileData versatileData) throws Exception {
        long l;
        long l2 = Math.round(versatileData.ask * this.decimalsConstant);
        long l3 = Math.round(versatileData.bid * this.decimalsConstant);
        if (l3 > l2 && l2 != 0L) {
            l = l2;
            l2 = l3;
            l3 = l;
        }
        if ((l = Math.round(versatileData.volume * this.volumeConstant)) < 0L) {
            l = Long.MAX_VALUE;
        }
        if (this.shouldWriteFullData()) {
            this.start = false;
            if (!this.isForceOldFormat()) {
                this.writeMagicChain(dataOutputStream);
            }
            this.fillLogicTypes(2, 2, 2, 2);
            this.fillDataTypes(3, 3, 3, 3);
            dataOutputStream.write(this.getConfigBytes(this.logicTypes, this.dataTypes));
            dataOutputStream.writeLong(versatileData.time);
            dataOutputStream.writeLong(l2);
            dataOutputStream.writeLong(l3);
            dataOutputStream.writeLong(l);
        } else {
            long l4 = versatileData.time - this.prevTime;
            long l5 = l2 - this.prevAsk;
            long l6 = l3 - this.prevBid;
            long l7 = l - this.prevVolume;
            this.fillLogicTypes(TickDataWriter.getLogicType(l4), TickDataWriter.getLogicType(l5), TickDataWriter.getLogicType(l6), TickDataWriter.getLogicType(l7));
            this.fillDataTypes(TickDataWriter.getDataType(l4), TickDataWriter.getDataType(l5), TickDataWriter.getDataType(l6), TickDataWriter.getDataType(l7));
            dataOutputStream.write(this.getConfigBytes(this.logicTypes, this.dataTypes));
            this.writeValue(dataOutputStream, l4, this.dataTypes[0]);
            this.writeValue(dataOutputStream, l5, this.dataTypes[1]);
            this.writeValue(dataOutputStream, l6, this.dataTypes[2]);
            this.writeValue(dataOutputStream, l7, this.dataTypes[3]);
        }
        this.prevTime = versatileData.time;
        this.prevAsk = l2;
        this.prevBid = l3;
        this.prevVolume = l;
        this.nextSaved();
    }

    private void fillDataTypes(int n, int n2, int n3, int n4) {
        this.dataTypes[0] = n;
        this.dataTypes[1] = n2;
        this.dataTypes[2] = n3;
        this.dataTypes[3] = n4;
    }

    private void fillLogicTypes(int n, int n2, int n3, int n4) {
        this.logicTypes[0] = n;
        this.logicTypes[1] = n2;
        this.logicTypes[2] = n3;
        this.logicTypes[3] = n4;
    }

    public void putData(ByteBuffer byteBuffer, VersatileData versatileData) throws Exception {
        long l = Math.round(versatileData.ask * this.decimalsConstant);
        long l2 = Math.round(versatileData.bid * this.decimalsConstant);
        long l3 = Math.round(versatileData.volume * this.volumeConstant);
        if (this.shouldWriteFullData()) {
            this.start = false;
            if (!this.isForceOldFormat()) {
                this.writeMagicChain(byteBuffer);
            }
            this.fillLogicTypes(2, 2, 2, 2);
            this.fillDataTypes(3, 3, 3, 3);
            byteBuffer.put(this.getConfigBytes(this.logicTypes, this.dataTypes));
            byteBuffer.putLong(versatileData.time);
            byteBuffer.putLong(l);
            byteBuffer.putLong(l2);
            byteBuffer.putLong(l3);
        } else {
            long l4 = versatileData.time - this.prevTime;
            long l5 = l - this.prevAsk;
            long l6 = l2 - this.prevBid;
            long l7 = l3 - this.prevVolume;
            this.fillLogicTypes(TickDataWriter.getLogicType(l4), TickDataWriter.getLogicType(l5), TickDataWriter.getLogicType(l6), TickDataWriter.getLogicType(l7));
            this.fillDataTypes(TickDataWriter.getDataType(l4), TickDataWriter.getDataType(l5), TickDataWriter.getDataType(l6), TickDataWriter.getDataType(l7));
            byteBuffer.put(this.getConfigBytes(this.logicTypes, this.dataTypes));
            this.putValue(byteBuffer, l4, this.dataTypes[0]);
            this.putValue(byteBuffer, l5, this.dataTypes[1]);
            this.putValue(byteBuffer, l6, this.dataTypes[2]);
            this.putValue(byteBuffer, l7, this.dataTypes[3]);
        }
        this.prevTime = versatileData.time;
        this.prevAsk = l;
        this.prevBid = l2;
        this.prevVolume = l3;
        this.nextSaved();
    }

    public void putData(RandomAccessReaderOffheap randomAccessReaderOffheap, VersatileData versatileData) throws Exception {
        long l = Math.round(versatileData.ask * this.decimalsConstant);
        long l2 = Math.round(versatileData.bid * this.decimalsConstant);
        long l3 = Math.round(versatileData.volume * this.volumeConstant);
        if (this.shouldWriteFullData()) {
            this.start = false;
            if (!this.isForceOldFormat()) {
                this.writeMagicChain(randomAccessReaderOffheap);
            }
            this.fillLogicTypes(2, 2, 2, 2);
            this.fillDataTypes(3, 3, 3, 3);
            randomAccessReaderOffheap.put(this.getConfigBytes(this.logicTypes, this.dataTypes));
            randomAccessReaderOffheap.putLong(versatileData.time);
            randomAccessReaderOffheap.putLong(l);
            randomAccessReaderOffheap.putLong(l2);
            randomAccessReaderOffheap.putLong(l3);
        } else {
            long l4 = versatileData.time - this.prevTime;
            long l5 = l - this.prevAsk;
            long l6 = l2 - this.prevBid;
            long l7 = l3 - this.prevVolume;
            this.fillLogicTypes(TickDataWriter.getLogicType(l4), TickDataWriter.getLogicType(l5), TickDataWriter.getLogicType(l6), TickDataWriter.getLogicType(l7));
            this.fillDataTypes(TickDataWriter.getDataType(l4), TickDataWriter.getDataType(l5), TickDataWriter.getDataType(l6), TickDataWriter.getDataType(l7));
            randomAccessReaderOffheap.put(this.getConfigBytes(this.logicTypes, this.dataTypes));
            this.putValue(randomAccessReaderOffheap, l4, this.dataTypes[0]);
            this.putValue(randomAccessReaderOffheap, l5, this.dataTypes[1]);
            this.putValue(randomAccessReaderOffheap, l6, this.dataTypes[2]);
            this.putValue(randomAccessReaderOffheap, l7, this.dataTypes[3]);
        }
        this.prevTime = versatileData.time;
        this.prevAsk = l;
        this.prevBid = l2;
        this.prevVolume = l3;
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

