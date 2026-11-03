/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.newDataFormat.NewDataFormat;
import com.strategyquant.datalib.data.io.newDataFormat.RandomAccessReaderOffheap;
import java.io.DataOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;

public abstract class NewDataFormatWritter
extends NewDataFormat {
    private long savedCnt = 0L;
    public static final byte[] BLOCK_START_MAGIC = new byte[15];

    public NewDataFormatWritter(boolean bl) {
        super(bl);
    }

    protected void writeMagicChain(DataOutputStream dataOutputStream) throws IOException {
        dataOutputStream.write(BLOCK_START_MAGIC, 0, BLOCK_START_MAGIC.length);
        int n = (int)((this.savedCnt + 1L) / 1000L);
        dataOutputStream.writeInt(n);
    }

    protected void writeMagicChain(ByteBuffer byteBuffer) {
        byteBuffer.put(BLOCK_START_MAGIC);
    }

    protected void writeMagicChain(RandomAccessReaderOffheap randomAccessReaderOffheap) {
        randomAccessReaderOffheap.put(BLOCK_START_MAGIC);
    }

    protected boolean shouldSaveStartChain() {
        return this.savedCnt % 1000L == 0L;
    }

    protected void nextSaved() {
        ++this.savedCnt;
    }

    protected boolean shouldWriteFullData() {
        return this.start || !this.isForceOldFormat() && this.shouldSaveStartChain();
    }

    public long getSavedCount() {
        return this.savedCnt;
    }

    static {
        for (int i = 0; i < BLOCK_START_MAGIC.length; ++i) {
            NewDataFormatWritter.BLOCK_START_MAGIC[i] = (byte)i;
        }
    }
}

