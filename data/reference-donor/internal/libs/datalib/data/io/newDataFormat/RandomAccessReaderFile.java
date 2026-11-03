/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.newDataFormat.IRandomAccessReader;
import java.io.EOFException;
import java.io.File;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;

public class RandomAccessReaderFile
implements IRandomAccessReader {
    private int bufferSize = 65536;
    private ByteBuffer buffer;
    private FileChannel fileChannel;
    private RandomAccessFile file;
    private String filePath;
    private long index = 0L;

    public RandomAccessReaderFile(String string) throws Exception {
        this.filePath = string;
        File file = new File(string);
        if (!file.exists()) {
            throw new Exception("File '" + string + "' doesn't exist");
        }
        if (file.length() == 0L) {
            throw new Exception("File '" + string + "' is empty");
        }
    }

    public void openFile() throws IOException {
        this.file = new RandomAccessFile(this.filePath, "r");
        this.file.seek(0L);
        this.buffer = ByteBuffer.allocateDirect(this.bufferSize);
        this.fileChannel = this.file.getChannel();
        this.fileChannel.read(this.buffer);
        this.buffer.flip();
    }

    public void closeFile() throws IOException {
        this.fileChannel.close();
        this.file.close();
    }

    private void ensureData(int n, boolean bl) throws IOException {
        if (this.buffer.remaining() < n) {
            this.buffer.compact();
            int n2 = this.fileChannel.read(this.buffer);
            this.buffer.flip();
            if (n2 <= 0) {
                throw new EOFException();
            }
        }
        if (bl) {
            this.index += (long)n;
        }
    }

    @Override
    public boolean dataRemaining() {
        int n = this.buffer.remaining();
        if (n > 0) {
            return true;
        }
        try {
            this.ensureData(1, false);
        }
        catch (IOException iOException) {
            return false;
        }
        return this.buffer.remaining() > 0;
    }

    @Override
    public byte readByte() throws IOException {
        this.ensureData(1, true);
        return this.buffer.get();
    }

    @Override
    public void readBytes(byte[] byArray) throws IOException {
        this.ensureData(byArray.length, true);
        this.buffer.get(byArray);
    }

    @Override
    public short readShort() throws IOException {
        this.ensureData(2, true);
        return this.buffer.getShort();
    }

    @Override
    public int readInt() throws IOException {
        this.ensureData(4, true);
        return this.buffer.getInt();
    }

    @Override
    public long readLong() throws IOException {
        this.ensureData(8, true);
        return this.buffer.getLong();
    }

    @Override
    public double readDouble() throws IOException {
        this.ensureData(8, true);
        return this.buffer.getDouble();
    }

    @Override
    public String readUTF() throws IOException {
        this.ensureData(2, true);
        this.buffer.get();
        byte by = this.buffer.get();
        byte[] byArray = new byte[by];
        this.ensureData(by, true);
        this.buffer.get(byArray);
        return new String(byArray);
    }

    @Override
    public float readFloat() throws IOException {
        this.ensureData(4, true);
        return this.buffer.getFloat();
    }

    @Override
    public void seek(long l) throws IOException {
        this.index = l;
        this.file.seek(l);
        this.buffer.clear();
        this.fileChannel.read(this.buffer);
        this.buffer.flip();
    }

    @Override
    public long getLength() throws IOException {
        return this.file.length();
    }

    @Override
    public long getPosition() throws IOException {
        return this.index;
    }
}

