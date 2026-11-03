/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.bartype.BarType
 *  com.strategyquant.datalib.bartype.BarTypeFactory
 *  com.strategyquant.datalib.bartype.BarTypeStatus
 *  com.strategyquant.datalib.broker.BrokerDto
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.DateShifter
 *  com.strategyquant.datalib.data.io.IDataLoader
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.ticksimulator.DefaultTickSimulator
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.historyData.ICryptable
 *  com.strategyquant.lib.utils.IProgressListener
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataManager.impl.Data.job;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.bartype.BarType;
import com.strategyquant.datalib.bartype.BarTypeFactory;
import com.strategyquant.datalib.bartype.BarTypeStatus;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.DateShifter;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.ticksimulator.DefaultTickSimulator;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.historyData.ICryptable;
import com.strategyquant.lib.utils.IProgressListener;
import java.io.File;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MT5Exporter {
    private static final int REFRESH_RATE = 100;
    public static final Logger Log = LoggerFactory.getLogger(MT5Exporter.class);
    private volatile boolean canceled;
    private boolean paused;
    private IProgressListener listener;
    private DataInfo dataInfo;
    private int decimals = 6;
    private DateShifter dateShifter;

    public void exportData(IProgressListener listener, String connection, String symbol, String timeframe, String spreadType, double spreadPoints, double spreadPips, String filePath, long fromDate, long toDate, String targetTimezone) {
        this.canceled = false;
        this.listener = listener;
        try {
            if (!timeframe.equals("TICK") && !timeframe.equals("M1")) {
                throw new Exception(L.t((String)"Export to MT5 works only with TICK and M1 data.", (Object[])new Object[0]));
            }
            this.dataInfo = DataManager.getDataInfo((String)connection, (String)symbol);
            this.decimals = this.dataInfo.symbolInfo.decimals;
            this.evalTimeZones(this.dataInfo, targetTimezone);
            listener.onStart();
            File f = new File(filePath);
            if (!f.exists()) {
                f.getParentFile().mkdirs();
            }
            if (timeframe.equals("TICK") || spreadType.equals("pips") || spreadType.equals("points")) {
                this.exportTickOrM1WithFixedSpread(listener, connection, symbol, this.dataInfo, timeframe, spreadType, spreadPoints, spreadPips, filePath, fromDate, toDate);
            } else {
                this.exportM1WithRealSpread(listener, connection, symbol, this.dataInfo, filePath, fromDate, toDate);
            }
            listener.onProgress(100.0);
            listener.setMessage(L.t((String)"Completed", (Object[])new Object[0]));
            listener.onFinish();
        }
        catch (Exception e) {
            Log.error("Error while exporting data to MT5. Exc.", (Throwable)e);
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

    private void exportTickOrM1WithFixedSpread(IProgressListener listener, String connection, String symbol, DataInfo dataInfo, String timeframe, String spreadType, double spreadPoints, double spreadPips, String filePath, long fromDate, long toDate) throws Exception {
        ChartDef chartDef = new ChartDef(connection, symbol, timeframe, fromDate, toDate, 2.5, "No Session");
        IDataLoader loader = DataManager.getDataLoader((ChartDef)chartDef, (int)1);
        loader.open();
        DataManager.checkDataExport((ICryptable)loader, (int)this.dataInfo.source);
        int totalRows = dataInfo.rows;
        RandomAccessFile file = new RandomAccessFile(filePath, "rw");
        file.setLength(0L);
        ByteBuffer buffer = ByteBuffer.allocate(65536);
        VersatileData data = new VersatileData();
        int rows = 0;
        while (loader.hasNextTick() && !this.canceled) {
            int volume;
            this.checkPaused();
            data.reset();
            loader.getNextTick(data);
            this.dateShifter.transformToTimeZone(data);
            String line = "";
            int n = volume = data.volume > 1.0 ? SQUtils.round((double)data.volume) : 1;
            if (data.type == 2) {
                String date = SQTime.formatDate((long)data.time);
                String time = SQTime.formatTime((long)data.time);
                double spread = spreadType.equals("pips") ? spreadPips * 10.0 : spreadPoints;
                line = date + "," + time + "," + this.d(data.open) + "," + this.d(data.high) + "," + this.d(data.low) + "," + this.d(data.close) + "," + volume + "," + volume + "," + SQUtils.round((double)spread) + "\n";
            } else {
                String dateTime = SQTime.toFullDateTimeString((long)data.time);
                Double tickSpreadPoints = null;
                if (spreadType.equals("pips")) {
                    tickSpreadPoints = spreadPips * 10.0;
                } else if (spreadType.equals("points")) {
                    tickSpreadPoints = spreadPoints;
                }
                if (tickSpreadPoints != null) {
                    double spreadPrice = tickSpreadPoints * dataInfo.symbolInfo.tickStep;
                    double mid = (data.bid + data.ask) / 2.0;
                    double halfSpread = spreadPrice / 2.0;
                    double bid_export = mid - halfSpread;
                    double ask_export = mid + halfSpread;
                    line = dateTime + "," + this.d(bid_export) + "," + this.d(ask_export) + "\n";
                } else {
                    line = dateTime + "," + this.d(data.bid) + "," + this.d(data.ask) + "\n";
                }
            }
            buffer.put(line.getBytes());
            ++rows;
            if (buffer.remaining() < 100) {
                buffer.flip();
                file.getChannel().write(buffer);
                buffer.clear();
            }
            if (rows % 100 != 0) continue;
            listener.setMessage(L.t((String)"Exported to MT5 %s", (Object[])new Object[]{SQTime.toDateMinuteString((long)data.time)}));
            listener.onProgress(SQUtils.round((double)((double)rows / (double)totalRows * 100.0), (int)1));
        }
        if (buffer.position() > 0) {
            buffer.flip();
            file.getChannel().write(buffer);
            buffer.clear();
        }
        loader.close();
        file.close();
    }

    private String d(double value) {
        return SQUtils.d2String((double)value, (int)this.decimals);
    }

    private void exportM1WithRealSpread(IProgressListener listener, String connection, String symbol, DataInfo dataInfo, String filePath, long fromDate, long toDate) throws Exception {
        ChartDef chartDef = new ChartDef(connection, symbol, "TICK", fromDate, toDate, 2.5, "No Session");
        IDataLoader loader = DataManager.getDataLoader((ChartDef)chartDef, (int)1);
        loader.open();
        DataManager.checkDataExport((ICryptable)loader, (int)dataInfo.source);
        int totalRows = dataInfo.rows;
        RandomAccessFile file = new RandomAccessFile(filePath, "rw");
        ByteBuffer buffer = ByteBuffer.allocate(65536);
        VersatileData loadedData = new VersatileData();
        BarTypeStatus barTypeStatus = new BarTypeStatus();
        DefaultTickSimulator tickSimulator = new DefaultTickSimulator();
        TickEvent tick = new TickEvent();
        VersatileData barData = new VersatileData();
        BarType targetBarType = BarTypeFactory.getBarType((String)"M1", (int)dataInfo.barTimeType);
        targetBarType = targetBarType.clone(targetBarType.getTimeframe());
        int rows = 0;
        boolean unwrittenBar = false;
        while (loader.hasNextTick() && !this.canceled) {
            this.checkPaused();
            loader.getNextTick(loadedData);
            this.dateShifter.transformToTimeZone(loadedData);
            loadedData.spread = -1.0;
            tickSimulator.init(loadedData);
            while (tickSimulator.getNextTick(tick)) {
                targetBarType.processTick(tick, barTypeStatus, 1);
                if (barTypeStatus.status == 0) {
                    this.writeData(file, buffer, barData);
                    unwrittenBar = false;
                    continue;
                }
                if (barTypeStatus.status == 1) {
                    this.writeData(file, buffer, barData);
                    this.initBarData(barData, barTypeStatus.barTime, tick.getAsk(), tick.getBid(), tick.getVolume());
                    unwrittenBar = true;
                    continue;
                }
                this.updateBarData(barData, tick.getAsk(), tick.getBid(), tick.getVolume());
            }
            if (++rows % 100 != 0) continue;
            listener.setMessage(L.t((String)"Exported to MT5 %s", (Object[])new Object[]{SQTime.toDateMinuteString((long)loadedData.time)}));
            listener.onProgress(SQUtils.round((double)((double)rows / (double)totalRows * 100.0), (int)1));
        }
        if (unwrittenBar) {
            this.writeData(file, buffer, barData);
        }
        if (buffer.position() > 0) {
            buffer.flip();
            file.getChannel().write(buffer);
            buffer.clear();
        }
        loader.close();
        file.close();
    }

    private void writeData(RandomAccessFile file, ByteBuffer buffer, VersatileData data) throws Exception {
        if (data.time == -1L || data.time == Long.MIN_VALUE) {
            return;
        }
        String line = "";
        String date = SQTime.formatDate((long)data.time);
        String time = SQTime.formatTime((long)data.time);
        int spread = new Double(data.spread / this.dataInfo.symbolInfo.tickStep).intValue();
        line = date + "," + time + "," + this.d(data.open) + "," + this.d(data.high) + "," + this.d(data.low) + "," + this.d(data.close) + "," + SQUtils.round2((double)data.volume) + "," + SQUtils.round2((double)data.volume) + "," + spread + "\n";
        buffer.put(line.getBytes());
        if (buffer.remaining() < 100) {
            buffer.flip();
            file.getChannel().write(buffer);
            buffer.clear();
        }
    }

    private void updateBarData(VersatileData barData, double ask, double bid, double volume) {
        if (bid > barData.high) {
            barData.high = bid;
        }
        if (bid < barData.low) {
            barData.low = bid;
        }
        barData.close = bid;
        barData.volume += volume;
        double spread = ask - bid;
        if (spread > barData.spread) {
            barData.spread = spread;
        }
    }

    private void initBarData(VersatileData barData, long time, double ask, double bid, double volume) {
        barData.time = time;
        barData.open = bid;
        barData.high = bid;
        barData.low = bid;
        barData.close = bid;
        barData.volume = volume;
        barData.spread = ask - bid;
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

