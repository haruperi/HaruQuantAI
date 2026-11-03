/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.newDataFormat.IRandomAccessReader;
import java.io.IOException;
import java.nio.ByteBuffer;

public class RandomAccessReaderArray
implements IRandomAccessReader {
    private long size;
    private ByteBuffer buffer;

    public RandomAccessReaderArray(byte[] byArray) {
        this.size = byArray.length;
        this.buffer = ByteBuffer.wrap(byArray);
    }

    @Override
    public boolean dataRemaining() {
        try {
            return this.getPosition() < this.size;
        }
        catch (Exception exception) {
            throw new RuntimeException("Exc.", exception);
        }
    }

    @Override
    public byte readByte() throws IOException {
        return this.buffer.get();
    }

    @Override
    public void readBytes(byte[] byArray) throws IOException {
        this.buffer.get(byArray);
    }

    @Override
    public short readShort() throws IOException {
        return this.buffer.getShort();
    }

    @Override
    public int readInt() throws IOException {
        return this.buffer.getInt();
    }

    @Override
    public long readLong() throws IOException {
        return this.buffer.getLong();
    }

    @Override
    public String readUTF() throws IOException {
        this.readByte();
        byte by = this.readByte();
        byte[] byArray = new byte[by];
        this.readBytes(byArray);
        return new String(byArray);
    }

    @Override
    public double readDouble() throws IOException {
        return this.buffer.getDouble();
    }

    @Override
    public float readFloat() throws IOException {
        return this.buffer.getFloat();
    }

    @Override
    public void seek(long l) throws IOException {
        this.buffer.position((int)l);
    }

    @Override
    public long getPosition() throws IOException {
        return this.buffer.position();
    }

    @Override
    public long getLength() throws IOException {
        return this.size;
    }
}

