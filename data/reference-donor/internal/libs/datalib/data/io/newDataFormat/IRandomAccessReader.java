/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import java.io.IOException;

public interface IRandomAccessReader {
    public boolean dataRemaining();

    public byte readByte() throws IOException;

    public void readBytes(byte[] var1) throws IOException;

    public short readShort() throws IOException;

    public int readInt() throws IOException;

    public long readLong() throws IOException;

    public String readUTF() throws IOException;

    public double readDouble() throws IOException;

    public float readFloat() throws IOException;

    public void seek(long var1) throws IOException;

    public long getPosition() throws IOException;

    public long getLength() throws IOException;
}

