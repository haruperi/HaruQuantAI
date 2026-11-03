/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.broker.BrokerDto
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.DateShifter
 *  com.strategyquant.datalib.data.io.IDataLoader
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.historyData.ICryptable
 *  com.strategyquant.lib.utils.IProgressListener
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.DateShifter;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.historyData.ICryptable;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.format.Format;
import java.io.File;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CsvExporter {
    private static final int REFRESH_RATE = 100;
    public static final Logger Log = LoggerFactory.getLogger(CsvExporter.class);
    private volatile boolean canceled;
    private boolean paused;
    private IProgressListener listener;
    private DateShifter dateShifter;

    public void exportData(IProgressListener listener, String connection, String symbol, String timeframe, String session, String filePath, long fromDate, long toDate, Format format, String targetTimezone) {
        int rows = 0;
        this.canceled = false;
        this.listener = listener;
        try {
            String line;
            listener.onStart();
            ChartDef chartDef = new ChartDef(connection, symbol, timeframe, fromDate, toDate, 2.5, session);
            IDataLoader loader = DataManager.getDataLoader((ChartDef)chartDef, (int)1);
            loader.open();
            DataInfo dataInfo = DataManager.getDataInfo((String)connection, (String)symbol);
            this.evalTimeZones(dataInfo, targetTimezone);
            DataManager.checkDataExport((ICryptable)loader, (int)dataInfo.source);
            int totalRows = dataInfo.rows;
            File f = new File(filePath);
            if (!f.exists()) {
                f.getParentFile().mkdirs();
            }
            RandomAccessFile file = new RandomAccessFile(filePath, "rw");
            ByteBuffer buffer = ByteBuffer.allocate(65536);
            VersatileData data = new VersatileData();
            if (format.includeHeader) {
                line = format.printHeader() + "\n";
                buffer.put(line.getBytes());
                buffer.flip();
                file.getChannel().write(buffer);
                buffer.clear();
            }
            while (loader.hasNextTick() && !this.canceled) {
                this.checkPaused();
                data.reset();
                loader.getNextTick(data);
                this.dateShifter.transformToTimeZone(data);
                line = format.printData(symbol, data, dataInfo.symbolInfo.decimals) + "\n";
                buffer.put(line.getBytes());
                ++rows;
                if (buffer.remaining() < 200) {
                    buffer.flip();
                    file.getChannel().write(buffer);
                    buffer.clear();
                }
                if (rows % 100 != 0) continue;
                listener.setMessage(L.t((String)"Exported to CSV %s", (Object[])new Object[]{SQTime.toDateMinuteString((long)data.time)}));
                listener.onProgress(SQUtils.round((double)((double)rows / (double)totalRows * 100.0), (int)1));
            }
            if (buffer.position() > 0) {
                buffer.flip();
                file.getChannel().write(buffer);
                buffer.clear();
            }
            listener.onProgress(100.0);
            listener.setMessage(L.t((String)"Completed", (Object[])new Object[0]));
            listener.onFinish();
            loader.close();
            file.close();
        }
        catch (Exception e) {
            Log.error("Error while exporting data", (Throwable)e);
            listener.onError(e.getMessage());
        }
    }

    private void evalTimeZones(DataInfo dataInfo, String targetTimezone) {
        String sourceTimezone = "UTC";
        if (dataInfo.brokerId != -1) {
            BrokerDto broker = BrokerManager.getInstance().getBroker(Integer.valueOf(dataInfo.brokerId));
            sourceTimezone = broker.getMtTimezone();
        }
        this.dateShifter = new DateShifter(sourceTimezone, targetTimezone);
    }

    private void checkPaused() throws InterruptedException {
        if (!this.paused) {
            return;
        }
        this.listener.onPause();
        while (this.paused && !this.canceled) {
            Thread.sleep(100L);
        }
        this.listener.onContinue();
    }

    public void pause() {
        this.paused = true;
    }

    public void restart() {
        this.paused = false;
    }

    public void cancel() {
        this.canceled = true;
    }
}

