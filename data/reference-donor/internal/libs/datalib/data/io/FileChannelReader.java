/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io;

import com.strategyquant.datalib.data.io.VersatileData;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;

public class FileChannelReader {
    private static final int BUFFER_SIZE = 65536;
    private ByteBuffer readerBuffer;
    private FileChannel readerFileChannel;
    private int dataSize = FileChannelReader.getDataSize();

    public FileChannelReader(FileChannel fileChannel, int n) {
        this.readerBuffer = ByteBuffer.allocate(65536);
        this.readerFileChannel = fileChannel;
        this.readerBuffer.clear();
        this.readerBuffer.flip();
    }

    public static int getDataSize() {
        return 40;
    }

    private void ensureData(int n) throws IOException {
        if (this.readerBuffer.remaining() < n) {
            this.readerBuffer.compact();
            if (this.readerFileChannel.read(this.readerBuffer) <= 0) {
                throw new IOException("Unexpected end-of-stream");
            }
            this.readerBuffer.flip();
        }
    }

    public long position() throws IOException {
        return this.readerFileChannel.position() - (long)this.readerBuffer.remaining();
    }

    public void position(long l) throws IOException {
        this.readerFileChannel.position(l);
        this.readerBuffer.clear();
        this.readerBuffer.flip();
    }

    public VersatileData getData(VersatileData versatileData) throws IOException {
        this.ensureData(this.dataSize);
        versatileData.time = this.readerBuffer.getLong();
        versatileData.ask = this.readerBuffer.getDouble();
        versatileData.bid = this.readerBuffer.getDouble();
        versatileData.volume = this.readerBuffer.getDouble();
        return versatileData;
    }
}

