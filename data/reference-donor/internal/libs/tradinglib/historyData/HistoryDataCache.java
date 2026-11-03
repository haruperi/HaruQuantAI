/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.historyData.dto.TickerDto
 *  com.strategyquant.datalib.historyData.dto.TickerKind
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.historyData;

import com.strategyquant.datalib.historyData.dto.TickerDto;
import com.strategyquant.datalib.historyData.dto.TickerKind;
import com.strategyquant.tradinglib.dukascopy.DownloadResultDto;
import com.strategyquant.tradinglib.historyData.DownloadMessageHandler;
import com.strategyquant.tradinglib.historyData.HistoryDataManager;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class HistoryDataCache {
    public static final Logger Log = LoggerFactory.getLogger(HistoryDataCache.class);
    private static final int BUFFER_SIZE = 2048;
    private Set<String> filesInCache = new HashSet<String>();
    private Map<String, byte[]> data = new HashMap<String, byte[]>();
    private String symbolForDownload;
    private String timeframe;
    private TickerKind kind;
    private Thread downloadThread;
    private volatile boolean stopped;
    private TickerDto ticker;

    public HistoryDataCache(String string, TickerDto tickerDto, TickerKind tickerKind, String string2) {
        this.symbolForDownload = string;
        this.timeframe = string2;
        this.kind = tickerKind;
        this.ticker = tickerDto;
    }

    public void stop() {
        this.stopped = true;
        if (this.downloadThread != null) {
            this.downloadThread.interrupt();
        }
    }

    public byte[] getDataFile(int n, int n2) {
        String string = this.timeframe.equals("M1") ? String.format("%04d%02d", n, n2) : String.format("%04d", n);
        return this.data.get(string);
    }

    public synchronized DownloadResultDto performLoad(int n, int n2, DownloadMessageHandler downloadMessageHandler) throws Exception {
        String string = HistoryDataManager.getZipDataFilename(n);
        if (this.filesInCache.contains(string)) {
            byte[] byArray = this.getDataFile(n, n2);
            return byArray == null ? DownloadResultDto.failed(-1) : DownloadResultDto.success(byArray, 0L);
        }
        this.downloadThread = Thread.currentThread();
        byte[] byArray = HistoryDataManager.get().downloadHistoryData(this.ticker, this.kind, n, n2, this.symbolForDownload, this.timeframe, downloadMessageHandler);
        if (byArray != null) {
            this.unzip(byArray, n, n2);
        }
        this.filesInCache.add(string);
        byte[] byArray2 = this.getDataFile(n, n2);
        return byArray2 == null ? DownloadResultDto.failed(-1, 0L, 0L) : DownloadResultDto.success(byArray2, 0L);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void unzip(byte[] byArray, int n, int n2) throws IOException {
        byte[] byArray2 = new byte[2048];
        ZipInputStream zipInputStream = new ZipInputStream(new ByteArrayInputStream(byArray));
        try {
            ZipEntry zipEntry = zipInputStream.getNextEntry();
            while (zipEntry != null) {
                int n3;
                if (this.stopped) {
                    return;
                }
                ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream((int)zipEntry.getSize());
                while ((n3 = zipInputStream.read(byArray2)) > 0) {
                    byteArrayOutputStream.write(byArray2, 0, n3);
                }
                byteArrayOutputStream.close();
                byte[] byArray3 = byteArrayOutputStream.toByteArray();
                this.storeContent(zipEntry.getName(), byArray3);
                zipEntry = zipInputStream.getNextEntry();
            }
        }
        finally {
            zipInputStream.closeEntry();
            zipInputStream.close();
        }
    }

    private void storeContent(String string, byte[] byArray) {
        string = string.split("\\.")[0];
        this.data.put(string, byArray);
    }
}

