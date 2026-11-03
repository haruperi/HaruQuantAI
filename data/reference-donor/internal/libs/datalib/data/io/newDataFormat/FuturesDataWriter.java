/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.FuturesVersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.NewDataFormatWritter;
import java.io.DataOutputStream;

public class FuturesDataWriter
extends NewDataFormatWritter {
    private long prevTime;
    private long prevOpen;
    private long prevHigh;
    private long prevLow;
    private long prevClose;
    private long prevVolume;
    private long prevOpenInterest;

    public FuturesDataWriter() {
        this(false);
    }

    public FuturesDataWriter(boolean bl) {
        super(bl);
    }

    public void writeData(DataOutputStream dataOutputStream, FuturesVersatileData futuresVersatileData) throws Exception {
        long l = Math.round(futuresVersatileData.open * this.decimalsConstant);
        long l2 = Math.round(futuresVersatileData.high * this.decimalsConstant);
        long l3 = Math.round(futuresVersatileData.low * this.decimalsConstant);
        long l4 = Math.round(futuresVersatileData.close * this.decimalsConstant);
        long l5 = Math.round(futuresVersatileData.volume * this.volumeConstant);
        long l6 = Math.round(futuresVersatileData.openInterest * this.volumeConstant);
        if (l5 < 0L) {
            l5 = Long.MAX_VALUE;
        }
        if (l6 < 0L) {
            l6 = Long.MAX_VALUE;
        }
        if (this.shouldWriteFullData()) {
            this.start = false;
            if (!this.isForceOldFormat()) {
                this.writeMagicChain(dataOutputStream);
            }
            int[] nArray = new int[]{2, 2, 2, 2, 2, 2, 2, 2};
            int[] nArray2 = new int[]{3, 3, 3, 3, 3, 3, 3, 0};
            dataOutputStream.write(this.getConfigBytes(nArray, nArray2));
            dataOutputStream.writeLong(futuresVersatileData.time);
            dataOutputStream.writeLong(l);
            dataOutputStream.writeLong(l2);
            dataOutputStream.writeLong(l3);
            dataOutputStream.writeLong(l4);
            dataOutputStream.writeLong(l5);
            dataOutputStream.writeLong(l6);
        } else {
            long l7 = futuresVersatileData.time - this.prevTime;
            long l8 = l - this.prevOpen;
            long l9 = l2 - this.prevHigh;
            long l10 = l3 - this.prevLow;
            long l11 = l4 - this.prevClose;
            long l12 = l5 - this.prevVolume;
            long l13 = l6 - this.prevOpenInterest;
            int[] nArray = new int[]{FuturesDataWriter.getLogicType(l7), FuturesDataWriter.getLogicType(l8), FuturesDataWriter.getLogicType(l9), FuturesDataWriter.getLogicType(l10), FuturesDataWriter.getLogicType(l11), FuturesDataWriter.getLogicType(l12), FuturesDataWriter.getLogicType(l13), 2};
            int[] nArray3 = new int[]{FuturesDataWriter.getDataType(l7), FuturesDataWriter.getDataType(l8), FuturesDataWriter.getDataType(l9), FuturesDataWriter.getDataType(l10), FuturesDataWriter.getDataType(l11), FuturesDataWriter.getDataType(l12), FuturesDataWriter.getDataType(l13), 0};
            dataOutputStream.write(this.getConfigBytes(nArray, nArray3));
            this.writeValue(dataOutputStream, l7, nArray3[0]);
            this.writeValue(dataOutputStream, l8, nArray3[1]);
            this.writeValue(dataOutputStream, l9, nArray3[2]);
            this.writeValue(dataOutputStream, l10, nArray3[3]);
            this.writeValue(dataOutputStream, l11, nArray3[4]);
            this.writeValue(dataOutputStream, l12, nArray3[5]);
            this.writeValue(dataOutputStream, l13, nArray3[6]);
        }
        this.prevTime = futuresVersatileData.time;
        this.prevOpen = l;
        this.prevHigh = l2;
        this.prevLow = l3;
        this.prevClose = l4;
        this.prevVolume = l5;
        this.prevOpenInterest = l6;
        this.nextSaved();
    }
}

