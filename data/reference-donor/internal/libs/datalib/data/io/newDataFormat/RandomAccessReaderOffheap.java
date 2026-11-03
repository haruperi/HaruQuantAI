/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.memory.OffHeapMemory
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.newDataFormat.IRandomAccessReader;
import com.strategyquant.lib.memory.OffHeapMemory;
import java.io.IOException;

public class RandomAccessReaderOffheap
implements IRandomAccessReader {
    private long address = -2L;
    private long index;
    private long size;

    public RandomAccessReaderOffheap(long l, long l2) throws Exception {
        this.address = l;
        this.size = l2;
        this.index = 0L;
    }

    @Override
    public final boolean dataRemaining() {
        return this.index < this.size;
    }

    @Override
    public final byte readByte() throws IOException {
        this.checkOffHeap();
        byte by = OffHeapMemory.getByte((long)(this.address + this.index));
        ++this.index;
        return by;
    }

    @Override
    public final void readBytes(byte[] byArray) throws IOException {
        this.checkOffHeap();
        for (int i = 0; i < byArray.length; ++i) {
            byArray[i] = OffHeapMemory.getByte((long)(this.address + this.index));
            ++this.index;
        }
    }

    @Override
    public final short readShort() throws IOException {
        this.checkOffHeap();
        short s = OffHeapMemory.getShort((long)(this.address + this.index));
        this.index += 2L;
        return s;
    }

    @Override
    public final int readInt() throws IOException {
        this.checkOffHeap();
        int n = OffHeapMemory.getInt((long)(this.address + this.index));
        this.index += 4L;
        return n;
    }

    @Override
    public final long readLong() throws IOException {
        this.checkOffHeap();
        long l = OffHeapMemory.getLong((long)(this.address + this.index));
        this.index += 8L;
        return l;
    }

    @Override
    public final String readUTF() throws IOException {
        this.readByte();
        byte by = this.readByte();
        byte[] byArray = new byte[by];
        this.readBytes(byArray);
        return new String(byArray);
    }

    public final void put(byte by) {
        this.checkOffHeap();
        OffHeapMemory.putByte((long)(this.address + this.index), (byte)by);
        ++this.index;
    }

    public final void putLong(long l) {
        this.checkOffHeap();
        OffHeapMemory.putLong((long)(this.address + this.index), (long)l);
        this.index += 8L;
    }

    public final void put(byte[] byArray) {
        this.checkOffHeap();
        for (int i = 0; i < byArray.length; ++i) {
            this.put(byArray[i]);
        }
    }

    public final void putInt(int n) {
        this.checkOffHeap();
        OffHeapMemory.putInt((long)(this.address + this.index), (int)n);
        this.index += 4L;
    }

    public final void putShort(short s) {
        this.checkOffHeap();
        OffHeapMemory.putShort((long)(this.address + this.index), (short)s);
        this.index += 2L;
    }

    public void checkOffHeap() {
        if (this.address < 0L) {
            OffHeapMemory.throwMemoryException((long)this.address);
        }
    }

    @Override
    public double readDouble() throws IOException {
        this.checkOffHeap();
        double d = OffHeapMemory.getDouble((long)(this.address + this.index));
        this.index += 8L;
        return d;
    }

    @Override
    public float readFloat() throws IOException {
        this.checkOffHeap();
        float f = OffHeapMemory.getFloat((long)(this.address + this.index));
        this.index += 4L;
        return f;
    }

    @Override
    public void seek(long l) throws IOException {
        this.index = l;
    }

    @Override
    public long getLength() throws IOException {
        return this.size;
    }

    @Override
    public long getPosition() throws IOException {
        return this.index;
    }
}

