/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.utils.IProgressListener
 *  org.joda.time.DateTime
 *  org.joda.time.DateTimeZone
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.data;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.ExchangeTimezone;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.datalib.historyData.dto.TickerDto;
import com.strategyquant.datalib.timezone.Timezone;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.utils.IProgressListener;
import java.io.File;
import org.joda.time.DateTime;
import org.joda.time.DateTimeZone;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataCloner {
    private static final int REFRESH_RATE = 100;
    public static final Logger Log = LoggerFactory.getLogger(DataCloner.class);
    private volatile boolean canceled = false;
    private boolean cloneRunning = false;
    private volatile boolean paused;
    private IProgressListener listener;
    private TickerDto ticker;
    private DataInfo sourceSymbolInfo;
    private DataInfo targetSymbolInfo;
    private int shiftHours;
    private boolean removeWeekends;
    private long dateFrom;
    private long dateTo;
    private int rows;
    private long secondsRecords;
    private DateTimeZone sourceTz;
    private DateTimeZone targetTz;
    private IDataLoader loader;
    private DataBinWriterNew writer;

    public void cancel() {
        this.canceled = true;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void cloneToTimezone(String string, String string2, String string3, int n, boolean bl, TickerDto tickerDto, IProgressListener iProgressListener) {
        try {
            this.ticker = tickerDto;
            this.canceled = false;
            this.cloneRunning = true;
            this.listener = iProgressListener;
            this.shiftHours = n;
            this.removeWeekends = bl;
            this.sourceSymbolInfo = DataManager.getDataInfo("History", string);
            this.targetSymbolInfo = DataManager.getDataInfo("History", string2);
            this.targetSymbolInfo.timezone = Timezone.shiftHours(string3, n);
            iProgressListener.setMessage(L.t((String)"Cloning '%s' data to timezone '%s'", (Object[])new Object[]{string, Timezone.print(this.targetSymbolInfo.timezone, this.targetSymbolInfo.source, false)}));
            this.cloneData();
        }
        catch (Exception exception) {
            Log.error("Error while cloning data. Exc.", (Throwable)exception);
            iProgressListener.onError(exception.getMessage());
        }
        finally {
            this.cloneRunning = false;
        }
    }

    private void cloneData() throws Exception {
        this.secondsRecords = 0L;
        this.dateFrom = 0L;
        this.dateTo = 0L;
        this.rows = 0;
        if (this.sourceSymbolInfo.rows > 0) {
            String string = DataManager.getDataFileName(this.sourceSymbolInfo.connection, this.targetSymbolInfo.symbol, this.sourceSymbolInfo.timeframe, "No Session");
            String string2 = DataManager.getTempFileName(string);
            this.prepareClone(string2);
            this.performCloneFile();
            this.loader.close();
            this.writer.close();
            DataManager.removeDataFiles(this.targetSymbolInfo.connection, this.targetSymbolInfo.symbol);
            new File(string2).renameTo(new File(string));
        }
        DataManager.updateData(this.targetSymbolInfo.connection, this.targetSymbolInfo.symbol, this.dateFrom, this.dateTo, this.rows, this.secondsRecords, this.sourceSymbolInfo.barTimeType, this.sourceSymbolInfo.timeframe, this.targetSymbolInfo.timezone, this.sourceSymbolInfo.id, this.removeWeekends);
        this.listener.onProgress(100.0);
        this.listener.onFinish();
    }

    private void prepareClone(String string) throws DataException, Exception {
        String string2;
        ChartDef chartDef = new ChartDef(this.sourceSymbolInfo.connection, this.sourceSymbolInfo.symbol, this.sourceSymbolInfo.timeframe, this.sourceSymbolInfo.dateFrom, this.sourceSymbolInfo.dateTo, 2.5, "No Session");
        this.loader = DataManager.getDataLoader(chartDef, 1);
        this.loader.open();
        boolean bl = this.loader.isCrypted();
        this.writer = null;
        this.writer = this.sourceSymbolInfo.timeframe.equals("TICK") ? (bl ? DataBinWriterNew.getCryptedInstance(2, MainApp.getDataPath(), this.sourceSymbolInfo.symbolInfo) : DataBinWriterNew.getInstance(2, MainApp.getDataPath(), this.sourceSymbolInfo.symbolInfo)) : (bl ? DataBinWriterNew.getCryptedInstance(1, MainApp.getDataPath(), this.sourceSymbolInfo.symbolInfo) : DataBinWriterNew.getInstance(1, MainApp.getDataPath(), this.sourceSymbolInfo.symbolInfo));
        this.writer.setFileName(string);
        this.writer.open();
        String string3 = this.sourceSymbolInfo.timezone != null ? this.sourceSymbolInfo.timezone : "Etc/UCT";
        String string4 = this.targetSymbolInfo.timezone;
        this.sourceTz = null;
        this.targetTz = null;
        if (!(this.sourceSymbolInfo.source != 6 && this.sourceSymbolInfo.source != 5 || string3 != null && !string3.startsWith("Exchange"))) {
            string2 = ExchangeTimezone.get().getTimezone(this.ticker.getMarketName());
            if (string3 != null && string3.length() > 8) {
                String string5 = string3.substring(8).trim();
                this.shiftHours += Integer.valueOf(string5).intValue();
            }
            this.sourceTz = DateTimeZone.forID((String)string2);
            if (string4.startsWith("Exchange")) {
                this.targetTz = DateTimeZone.forID((String)string2);
            }
        }
        if (this.sourceTz == null) {
            string2 = Timezone.parseId(string3);
            if (string2.equals("EETUS")) {
                string2 = "America/New_York";
                this.shiftHours -= 7;
            }
            this.sourceTz = DateTimeZone.forID((String)string2);
        }
        if (this.targetTz == null) {
            string2 = Timezone.parseId(string4);
            if (string2.equals("EETUS")) {
                string2 = "America/New_York";
                this.shiftHours += 7;
            }
            this.targetTz = DateTimeZone.forID((String)string2);
        }
    }

    private void performCloneFile() throws Exception, InterruptedException {
        VersatileData versatileData = new VersatileData();
        long l = -1L;
        while (this.loader.hasNextTick()) {
            int n;
            this.loader.getNextTick(versatileData);
            DateTime dateTime = new DateTime(versatileData.time).withZoneRetainFields(this.sourceTz);
            DateTime dateTime2 = dateTime.withZone(this.targetTz).toLocalDateTime().toDateTime();
            if (this.shiftHours != 0) {
                dateTime2 = dateTime2.plusHours(this.shiftHours);
            }
            versatileData.time = dateTime2.getMillis();
            if (versatileData.time < l) continue;
            l = versatileData.time;
            if (this.removeWeekends && ((n = dateTime2.getDayOfWeek()) == 6 || n == 7)) continue;
            if (this.dateFrom == 0L) {
                this.dateFrom = versatileData.time;
            }
            this.dateTo = versatileData.time;
            this.writer.writeData(versatileData);
            ++this.rows;
            if (this.rows % 100 == 0) {
                this.listener.onProgress((double)this.rows / (double)this.sourceSymbolInfo.rows * 100.0);
                this.listener.setMessage(L.t((String)"Cloned %s", (Object[])new Object[]{SQTime.toDateMinuteString((long)this.dateTo)}));
            }
            if (this.canceled) break;
            this.checkPaused();
        }
    }

    public void createSymbol(String string, DataInfo dataInfo) throws Exception {
        DataManager.addData(dataInfo.connection, string, dataInfo.instrument, dataInfo.barTimeType, dataInfo.source, dataInfo.uSymbol, dataInfo.uSymbolName, -1, dataInfo.brokerId);
    }

    public boolean isRunning() {
        return this.cloneRunning;
    }

    public void pause() {
        this.paused = true;
    }

    public void restart() {
        this.paused = false;
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
}

