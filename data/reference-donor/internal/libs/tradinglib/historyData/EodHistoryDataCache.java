/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.historyData;

import com.strategyquant.tradinglib.dukascopy.DownloadResultDto;
import com.strategyquant.tradinglib.historyData.DownloadMessageHandler;
import com.strategyquant.tradinglib.historyData.HistoryDataManager;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.locks.ReentrantLock;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class EodHistoryDataCache {
    public static final Logger Log = LoggerFactory.getLogger(EodHistoryDataCache.class);
    private static final int BUFFER_SIZE = 2048;
    private static EodHistoryDataCache instance = new EodHistoryDataCache();
    private Map<String, byte[]> data = new HashMap<String, byte[]>();
    private Thread downloadThread;
    private volatile boolean stopped;
    private Map<String, ReentrantLock> locks = new HashMap<String, ReentrantLock>();

    private EodHistoryDataCache() {
    }

    public void stop() {
        this.stopped = true;
        if (this.downloadThread != null) {
            this.downloadThread.interrupt();
        }
    }

    public byte[] getDataFile(String string, int n) throws IOException {
        return this.data.remove(HistoryDataManager.get().normalizeSymbol(string) + n);
    }

    public boolean exists(String string, int n) {
        return this.data.containsKey(HistoryDataManager.get().normalizeSymbol(string) + n);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public DownloadResultDto performLoad(String string, int n, int n2, DownloadMessageHandler downloadMessageHandler) throws Exception {
        byte[] byArray;
        if (this.exists(string, n)) {
            byte[] byArray2 = this.getDataFile(string, n);
            Log.debug("Adjusted data: {} already fetched to {}", (Object)string, (Object)n);
            return byArray2 == null ? DownloadResultDto.failed(-1) : DownloadResultDto.success(byArray2, 0L);
        }
        String string2 = HistoryDataManager.get().getAdjustedIdent(string);
        ReentrantLock reentrantLock = this.getLock(string2);
        try {
            reentrantLock.lock();
            if (this.exists(string, n)) {
                byte[] byArray3 = this.getDataFile(string, n);
                Log.debug("Adjusted data: {} already fetched for {}", (Object)string, (Object)n);
                DownloadResultDto downloadResultDto = byArray3 == null ? DownloadResultDto.failed(-1) : DownloadResultDto.success(byArray3, 0L);
                return downloadResultDto;
            }
            this.downloadThread = Thread.currentThread();
            Log.debug("Downloading adjusted data: {} - {}", (Object)string, (Object)string2);
            byArray = HistoryDataManager.get().downloadAdjustedHistoryData(string2, downloadMessageHandler);
            if (byArray != null) {
                this.unzip(byArray);
            }
            Log.debug("Downloaded adjusted data: {} - {}", (Object)string, (Object)string2);
        }
        finally {
            reentrantLock.unlock();
        }
        byArray = this.getDataFile(string, n);
        return byArray == null ? DownloadResultDto.failed(-1, 0L, 0L) : DownloadResultDto.success(byArray, 0L);
    }

    private synchronized ReentrantLock getLock(String string) {
        ReentrantLock reentrantLock = this.locks.get(string);
        if (reentrantLock == null) {
            reentrantLock = new ReentrantLock();
            this.locks.put(string, reentrantLock);
        }
        return reentrantLock;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void unzip(byte[] byArray) throws IOException {
        byte[] byArray2 = new byte[2048];
        ZipInputStream zipInputStream = new ZipInputStream(new ByteArrayInputStream(byArray));
        try {
            ZipEntry zipEntry = zipInputStream.getNextEntry();
            while (zipEntry != null) {
                String[] stringArray;
                int n;
                if (this.stopped) {
                    return;
                }
                ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream((int)zipEntry.getSize());
                while ((n = zipInputStream.read(byArray2)) > 0) {
                    byteArrayOutputStream.write(byArray2, 0, n);
                }
                byteArrayOutputStream.close();
                byte[] byArray3 = byteArrayOutputStream.toByteArray();
                if (byArray3.length > 0 && (stringArray = zipEntry.getName().split("/")).length == 2) {
                    this.storeContent(stringArray[0], stringArray[1], byArray3);
                }
                zipEntry = zipInputStream.getNextEntry();
            }
        }
        finally {
            zipInputStream.closeEntry();
            zipInputStream.close();
        }
    }

    public void reset() {
        this.data.clear();
        this.stopped = false;
    }

    private void storeContent(String string, String string2, byte[] byArray) throws IOException {
        String string3 = string2.substring(0, 4);
        this.data.put(string + ".D" + string3, byArray);
    }

    public static EodHistoryDataCache getInstance() {
        return instance;
    }
}

