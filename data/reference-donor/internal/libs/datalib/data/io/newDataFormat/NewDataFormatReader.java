/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.newDataFormat.IRandomAccessReader;
import com.strategyquant.datalib.data.io.newDataFormat.NewDataFormat;
import java.io.IOException;
import java.nio.ByteBuffer;

public abstract class NewDataFormatReader
extends NewDataFormat {
    private byte[] loadStartChainTmp = null;
    private long loadedCnt = 0L;
    private long dataStartPosition = 0L;
    private boolean newFormat;

    public NewDataFormatReader(boolean bl) {
        super(bl);
    }

    public void setDataStartPosition(long l) {
        this.dataStartPosition = l;
    }

    protected void checkFormat(IRandomAccessReader iRandomAccessReader) throws IOException {
        iRandomAccessReader.seek(this.dataStartPosition);
        this.newFormat = this.readMagicChain(iRandomAccessReader, true) != -1;
        iRandomAccessReader.seek(this.dataStartPosition);
    }

    protected void setNewFormat(boolean bl) {
        this.newFormat = bl;
    }

    protected boolean isNewFormat() {
        return this.newFormat;
    }

    public void seek(IRandomAccessReader iRandomAccessReader, long l) throws Exception {
        long l2;
        iRandomAccessReader.seek(this.dataStartPosition);
        int n = (int)(l / 1000L);
        if (n > 0) {
            l2 = this.gotoChain(iRandomAccessReader, n);
            iRandomAccessReader.seek(l2);
        }
        l2 = l - (long)(n * 1000);
        this.loadedCnt = n * 1000;
        this.start = false;
        this.newFormat = true;
        this.readAndTrashNRecords(l2, iRandomAccessReader);
    }

    protected boolean shouldLoadStartChain() {
        return this.loadedCnt % 1000L == 0L;
    }

    protected void nextLoaded() {
        ++this.loadedCnt;
    }

    protected int readMagicChain(IRandomAccessReader iRandomAccessReader, boolean bl) throws IOException {
        if (this.loadStartChainTmp == null) {
            this.loadStartChainTmp = new byte[15];
        }
        iRandomAccessReader.readBytes(this.loadStartChainTmp);
        int n = 0;
        if (bl) {
            for (int n2 : this.loadStartChainTmp) {
                if (n2 != n) {
                    return -1;
                }
                ++n;
            }
        }
        long l = iRandomAccessReader.getPosition();
        int n3 = iRandomAccessReader.readInt();
        return n3;
    }

    private long gotoChain(IRandomAccessReader iRandomAccessReader, int n) throws IOException {
        long l = iRandomAccessReader.getLength();
        int n2 = this.getMinimalChainSize();
        int n3 = this.getMaximalChainSize();
        long l2 = (long)n2 * (long)n;
        iRandomAccessReader.seek(l2);
        while (true) {
            long l3;
            if ((l3 = this.findNextChain(iRandomAccessReader, l2, l)) == -1L) {
                throw new IOException("Seek parameter is out of range");
            }
            iRandomAccessReader.seek(l3 + 15L);
            int n4 = this.getBlockIndex(iRandomAccessReader, l3 + 15L);
            if (n4 == n) {
                return l3;
            }
            int n5 = n - n4;
            int n6 = n5 > 0 ? n5 * n2 : n5 * n3;
            l2 = l3 + (long)n6;
            iRandomAccessReader.seek(l2);
        }
    }

    private int getMinimalChainSize() {
        return 1000 * this.getMinimalRecordSize() + 15;
    }

    private int getMaximalChainSize() {
        return 1000 * this.getMaximalRecordSize() + 15;
    }

    protected int getMinimalRecordSize() {
        return 1;
    }

    protected int getMaximalRecordSize() {
        return 1;
    }

    private long findNextChain(IRandomAccessReader iRandomAccessReader, long l, long l2) throws IOException {
        int n = 2048;
        int n2 = 0;
        long l3 = 0L;
        long l4;
        while ((l4 = l2 - l) >= 0L) {
            if (l4 < (long)n) {
                n = (int)l4;
            }
            byte[] byArray = new byte[n];
            iRandomAccessReader.readBytes(byArray);
            for (int i = 0; i < n; ++i) {
                int n3 = byArray[i];
                if (n3 == n2 || n3 == 0) {
                    if (n3 == 0) {
                        l3 = l + (long)i;
                        n2 = 0;
                    }
                    ++n2;
                } else {
                    n2 = 0;
                }
                if (n2 != 14) continue;
                return l3;
            }
            if (n != 2048) {
                return -1L;
            }
            l += (long)n;
        }
        return -1L;
    }

    private int getBlockIndex(IRandomAccessReader iRandomAccessReader, long l) throws IOException {
        iRandomAccessReader.seek(l - 20L);
        byte[] byArray = new byte[30];
        iRandomAccessReader.readBytes(byArray);
        iRandomAccessReader.seek(l);
        byte[] byArray2 = new byte[4];
        iRandomAccessReader.readBytes(byArray2);
        ByteBuffer byteBuffer = ByteBuffer.wrap(byArray2);
        return byteBuffer.getInt();
    }

    protected void readAndTrashNRecords(long l, IRandomAccessReader iRandomAccessReader) throws Exception {
    }
}

