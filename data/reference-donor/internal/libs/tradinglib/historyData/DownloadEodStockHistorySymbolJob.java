/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.data.DataCloner
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.ExchangeTimezone
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew
 *  com.strategyquant.datalib.historyData.dto.TickerDto
 *  com.strategyquant.datalib.historyData.dto.TickerKind
 *  com.strategyquant.datalib.timezone.Timezone
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.gridlib.compute.common.ExecuteOptions
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.exception.SQException
 *  com.strategyquant.lib.historyData.DataSources
 *  com.strategyquant.lib.historyData.HistoryDataSubscription
 *  com.strategyquant.lib.utils.IProgressListener
 *  org.joda.time.DateTime
 *  org.joda.time.DateTimeZone
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.historyData;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.DataCloner;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.ExchangeTimezone;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.datalib.historyData.dto.TickerDto;
import com.strategyquant.datalib.historyData.dto.TickerKind;
import com.strategyquant.datalib.timezone.Timezone;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.compute.common.ExecuteOptions;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.exception.SQException;
import com.strategyquant.lib.historyData.DataSources;
import com.strategyquant.lib.historyData.HistoryDataSubscription;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.tradinglib.dukascopy.DownloadResultDto;
import com.strategyquant.tradinglib.historyData.DownloadMessageHandler;
import com.strategyquant.tradinglib.historyData.EodHistoryDataCache;
import com.strategyquant.tradinglib.historyData.HistoryDataManager;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.sql.Date;
import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import org.joda.time.DateTime;
import org.joda.time.DateTimeZone;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DownloadEodStockHistorySymbolJob
extends GridJob<Void> {
    public static final String DOWNLOAD_GROUP = "HistoryDownloadPerformerGroup";
    public static final String DATE_TIME_FORMAT = "yyyy.MM.dd";
    private static final long serialVersionUID = 1L;
    public static final Logger Log = LoggerFactory.getLogger(DownloadEodStockHistorySymbolJob.class);
    private DataBinReaderNew reader;
    private DataBinWriterNew writer;
    private DataManagerProgressListener progressListener;
    private volatile boolean stopped;
    private volatile boolean paused;
    private ExecuteOptions executeOptions;
    private String timeframe;
    private String symbol;
    private TickerKind kind;
    private TickerDto ticker;
    private long downloadFromDate;
    private long fromDate;
    private long toDate;
    private long lastSavedDate;
    private int totalRecords;
    private EodHistoryDataCache dataCache;
    private int totalDays;
    private int performedDays;
    private List<VersatileData> datas = new LinkedList<VersatileData>();
    private boolean minutesShift;
    private int bartimeType;
    private DataInfo dataInfo;
    private int shiftHours = 0;
    private DateTimeZone sourceTz;
    private DateTimeZone targetTz;
    private boolean freeSymbol;
    private long timeShift;
    private long lastestDateFromFile;
    private String tickerForDownload;
    private TickerDto aliasTicker;
    private boolean forceDownload;

    public DownloadEodStockHistorySymbolJob(String string, DataInfo dataInfo, TickerKind tickerKind, TickerDto tickerDto, boolean bl) throws Exception {
        super(string, 0, null);
        String string2;
        this.forceDownload = bl;
        this.executeOptions = new ExecuteOptions();
        this.executeOptions.setMaxRunningCount(6);
        this.dataInfo = dataInfo;
        this.kind = tickerKind;
        this.symbol = dataInfo.symbol;
        this.timeframe = dataInfo.timeframe;
        this.bartimeType = dataInfo.barTimeType;
        this.minutesShift = dataInfo.barTimeType == 2 && this.timeframe.equals("M1");
        this.ticker = tickerDto;
        this.tickerForDownload = tickerDto.getTicker();
        Long l = tickerDto.getAliasTickerId();
        if (l != null) {
            TickerDto tickerDto2 = this.aliasTicker = tickerKind == TickerKind.STOCK ? HistoryDataManager.get().getStockTicker(l) : HistoryDataManager.get().getFutureTicker(l);
            if (this.aliasTicker != null) {
                this.tickerForDownload = this.aliasTicker.getTicker();
            }
        }
        this.freeSymbol = HistoryDataSubscription.getInstance().isFreeSymbol(dataInfo.uSymbol, tickerKind == TickerKind.FUTURES, this.timeframe.equals("D1"));
        try {
            string2 = ExchangeTimezone.get().getTimezone(tickerDto.getMarketName());
        }
        catch (NullPointerException nullPointerException) {
            string2 = ExchangeTimezone.get().getTimezone(tickerDto.getMarketName());
        }
        String string3 = dataInfo.timezone;
        String string4 = null;
        if (string3 == null || string3.startsWith("Exchange")) {
            string4 = string2;
            if (string3 != null && string3.length() > 8) {
                String string5 = string3.substring(8).trim();
                this.shiftHours = Integer.valueOf(string5);
            }
        } else {
            string4 = dataInfo.timezone;
        }
        if (string4.equals("EETUS")) {
            string4 = "America/New_York";
            this.shiftHours = 7;
        }
        this.sourceTz = DateTimeZone.forID((String)Timezone.parseId((String)string2));
        this.targetTz = DateTimeZone.forID((String)Timezone.parseId((String)string4));
        if (HistoryDataManager.get().shouldSetFixedTimeForEod(tickerDto, dataInfo.barTimeType)) {
            this.timeShift = HistoryDataManager.get().getEodShiftDate(tickerDto);
        } else if (HistoryDataManager.get().shouldShiftHoursForM1(tickerDto)) {
            this.timeShift = HistoryDataManager.get().getM1ShiftDate(tickerDto);
        }
    }

    private void checkPaused() throws InterruptedException {
        if (!this.paused) {
            return;
        }
        this.progressListener.onPause();
        while (this.paused && !this.stopped) {
            Thread.sleep(500L);
        }
        this.progressListener.onContinue();
    }

    private void prepareFiles() throws Exception {
        Log.debug("Preparing data files");
        String string = DataManager.getDataFileName((String)"History", (String)this.symbol, (String)this.timeframe, (String)"No Session");
        String string2 = string + ".copy";
        File file = new File(string);
        File file2 = new File(string2);
        if (file.exists()) {
            if (file.length() == 0L) {
                file.delete();
            } else {
                try {
                    Files.copy(file.toPath(), file2.toPath(), StandardCopyOption.REPLACE_EXISTING);
                    this.reader = DataBinReaderNew.getInstance((int)1, (InstrumentInfo)this.dataInfo.symbolInfo);
                    this.reader.setFileName(string2);
                    this.reader.openFile();
                }
                catch (Exception exception) {
                    Log.error("Cannot make a copy of existing symbol data file. ", (Throwable)exception);
                    this.reader = null;
                }
            }
        }
        try {
            this.writer = this.freeSymbol ? DataBinWriterNew.getInstance((int)1, (String)MainApp.getDataPath(), (InstrumentInfo)this.dataInfo.symbolInfo) : DataBinWriterNew.getCryptedInstance((int)1, (String)MainApp.getDataPath(), (InstrumentInfo)this.dataInfo.symbolInfo);
            this.writer.setFileName(string);
            this.writer.open();
        }
        catch (Exception exception) {
            Log.error("Cannot open symbol data file for writing. ", (Throwable)exception);
            throw new Exception(L.t((String)"Error - Cannot open symbol data file for writing.", (Object[])new Object[0]));
        }
    }

    public void setProgressListener(DataManagerProgressListener dataManagerProgressListener) {
        this.progressListener = dataManagerProgressListener;
    }

    public void messageReceived(GridMessage gridMessage) {
        super.messageReceived(gridMessage);
        switch (gridMessage.getMessageID()) {
            case 4: {
                this.stopped = true;
                this.dataCache.stop();
                this.progressListener.setMessage(L.t((String)"Stopping download - please wait", (Object[])new Object[0]));
                break;
            }
            case 2: {
                this.paused = true;
                break;
            }
            case 3: {
                this.paused = false;
            }
        }
    }

    private void correctTickData(VersatileData versatileData) {
        if (versatileData.open == 0.0) {
            versatileData.open = this.getNonZero(versatileData);
        }
        if (versatileData.high == 0.0) {
            versatileData.high = this.getNonZero(versatileData);
        }
        if (versatileData.low == 0.0) {
            versatileData.low = this.getNonZero(versatileData);
        }
        if (versatileData.close == 0.0) {
            versatileData.close = this.getNonZero(versatileData);
        }
    }

    private double getNonZero(VersatileData versatileData) {
        if (versatileData.open != 0.0) {
            return versatileData.open;
        }
        if (versatileData.high != 0.0) {
            return versatileData.high;
        }
        if (versatileData.low != 0.0) {
            return versatileData.low;
        }
        return versatileData.close;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public Void call() throws Exception {
        long l;
        String string = MainApp.settings().get("cdnPreferred", DataSources.DOWNLOAD_TYPE_CDN);
        Log.debug("Downloading symbol: {}, from: {}", (Object)this.dataInfo.symbol, (Object)string);
        long l2 = this.dataInfo.dateTo;
        long l3 = l = this.aliasTicker != null ? this.aliasTicker.getDateTo().getTime() : this.ticker.getDateTo().getTime();
        if (l <= l2) {
            this.updateProgress(L.t((String)"Completed", (Object[])new Object[0]), true, true);
            return null;
        }
        try {
            Object object;
            boolean bl;
            this.progressListener.onProgress(0.2);
            this.progressListener.setMessage(L.t((String)"Preparing download", (Object[])new Object[0]));
            Log.debug("Starting: {}", (Object)Thread.currentThread().getName());
            if (this.stopped) {
                this.setFinishProgress(L.t((String)"Stopped", (Object[])new Object[0]));
                Void void_ = null;
                return void_;
            }
            this.prepareFiles();
            this.evalDates();
            String string2 = this.ticker.getName() != null ? this.ticker.getName() : this.ticker.getTicker();
            boolean bl2 = bl = !string2.equals(this.dataInfo.uSymbolName);
            if (this.fromDate == -1L) {
                throw new RuntimeException(L.t((String)"Data for this timeframe are not available", (Object[])new Object[0]));
            }
            this.dataCache = EodHistoryDataCache.getInstance();
            Log.debug("Downloading data from: {}, to: {}", (Object)SQTime.toDateString((long)this.downloadFromDate), (Object)SQTime.toDateString((long)this.toDate));
            long l4 = this.downloadFromDate;
            this.lastSavedDate = -1L;
            l4 = SQTime.setDayOfMonth((long)l4, (int)1);
            long l5 = this.getDownloadLimit(this.toDate);
            while (!this.stopped && l4 <= l5) {
                object = this.getForDay(l4);
                if (((DownloadResultDto)object).getData() != null) {
                    this.write(((DownloadResultDto)object).getData());
                }
                this.checkPaused();
                long l6 = l4;
                l4 = this.timeframe.equals("M1") ? SQTime.addMonths((long)l4, (int)1) : SQTime.addYears((long)l4, (int)1);
                int n = SQTime.getDaysBetween((long)l6, (long)l4);
                this.performedDays += n;
            }
            if (bl) {
                DataManager.updateUnderlyingSymbolName((String)this.dataInfo.connection, (String)this.dataInfo.symbol, (String)string2);
            }
            if (this.lastSavedDate == -1L && this.lastestDateFromFile > 0L) {
                this.lastSavedDate = this.lastestDateFromFile;
            }
            this.finish(this.lastSavedDate);
            this.closeFiles(true);
            this.recomputeClonedData();
            object = this.stopped ? L.t((String)"Stopped", (Object[])new Object[0]) : L.t((String)"Completed", (Object[])new Object[0]);
            this.setFinishProgress((String)object);
        }
        catch (SQException sQException) {
            Log.error("Error while performing history data import", (Throwable)sQException);
            this.onError(sQException.getMessage());
        }
        catch (Throwable throwable) {
            Log.error("Error while performing history data import", throwable);
            this.onError(L.t((String)"Error while performing history data import", (Object[])new Object[0]));
        }
        finally {
            DataManagerDataProgress.get().removeListener(this.symbol);
            Log.debug("Download job for symbol: {} finished", (Object)this.symbol);
        }
        return null;
    }

    private void recomputeClonedData() {
        try {
            DataCloner dataCloner = new DataCloner();
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)this.dataInfo.symbol);
            ArrayList arrayList = DataManager.listCloned((int)dataInfo.id);
            for (int i = 0; i < arrayList.size(); ++i) {
                DataInfo dataInfo2 = (DataInfo)arrayList.get(i);
                DataManager.clearData((String)dataInfo2.connection, (String)dataInfo2.symbol);
                this.progressListener.setMessage(L.t((String)"Recomputing cloned data", (Object[])new Object[0]));
                String[] stringArray = dataInfo2.timezone.split("\\|");
                String string = stringArray[0];
                int n = 0;
                try {
                    n = Integer.parseInt(stringArray[1]);
                }
                catch (Exception exception) {
                    // empty catch block
                }
                dataCloner.cloneToTimezone(this.dataInfo.symbol, dataInfo2.symbol, string, n, dataInfo2.removeWeekends, this.ticker, (IProgressListener)this.progressListener);
            }
        }
        catch (Exception exception) {
            Log.error("Error while recomputing cloned data.", (Throwable)exception);
            this.onError(L.t((String)"Error while recomputing cloned data.", (Object[])new Object[0]));
        }
    }

    private long getDownloadLimit(long l) {
        if (this.timeframe.equals("M1")) {
            l = SQTime.setDayOfMonth((long)l, (int)1);
            l = SQTime.addMonths((long)l, (int)1);
            l = SQTime.addDays((long)l, (int)-1);
            return l;
        }
        l = SQTime.addYears((long)l, (int)1);
        l = SQTime.setMonthOfYear((long)l, (int)1);
        l = SQTime.setDayOfMonth((long)l, (int)1);
        l = SQTime.addDays((long)l, (int)-1);
        return l;
    }

    public void setFinishProgress(String string) {
        this.performedDays = this.totalDays;
        this.updateProgress(string, true, true);
    }

    private void updateProgress(String string, boolean bl, boolean bl2) {
        if (this.progressListener != null) {
            double d = SQUtils.round((double)((double)this.performedDays * 100.0 / (double)this.totalDays), (int)1);
            if (bl) {
                d = 100.0;
            }
            if (d < 100.0 || bl) {
                this.progressListener.onProgress(d);
            }
            if (this.stopped) {
                string = L.t((String)"Stopping", (Object[])new Object[0]) + " - " + string;
            }
            this.progressListener.setMessage(string);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private List<VersatileData> getVersatileDataForStock(byte[] byArray) throws Exception {
        DataBinReaderNew dataBinReaderNew = DataBinReaderNew.getInstance((int)1, (InstrumentInfo)this.dataInfo.symbolInfo);
        dataBinReaderNew.setData(byArray);
        long l = -1L;
        VersatileData versatileData = new LinkedList();
        try {
            VersatileData versatileData2;
            while (dataBinReaderNew.readData()) {
                if (dataBinReaderNew.tickData.time < this.downloadFromDate || l >= dataBinReaderNew.tickData.time) continue;
                versatileData2 = this.createData(dataBinReaderNew.tickData);
                this.correctTickData(versatileData2);
                versatileData.add(versatileData2);
                this.storeStockVersatileDataToQueue(versatileData2);
                l = versatileData2.time;
            }
            versatileData2 = versatileData;
            return versatileData2;
        }
        finally {
            dataBinReaderNew.closeFile();
        }
    }

    private VersatileData createData(VersatileData versatileData) {
        VersatileData versatileData2 = new VersatileData();
        versatileData2.time = versatileData.time;
        versatileData2.close = versatileData.close;
        versatileData2.open = versatileData.open;
        versatileData2.low = versatileData.low;
        versatileData2.high = versatileData.high;
        versatileData2.volume = versatileData.volume;
        return versatileData2;
    }

    private void storeStockVersatileDataToQueue(VersatileData versatileData) {
        if (versatileData.open != -1.0 || versatileData.high == -1.0) {
            // empty if block
        }
        this.datas.add(0, versatileData);
    }

    private void write(byte[] byArray) throws Exception {
        this.writeStocks(byArray);
    }

    private void writeStocks(byte[] byArray) throws Exception {
        List<VersatileData> list = this.getVersatileDataForStock(byArray);
        this.shiftTimeIfRequired(list);
        for (VersatileData versatileData : list) {
            this.writer.writeData(versatileData);
            this.lastSavedDate = versatileData.time;
            ++this.totalRecords;
        }
    }

    private void shiftTimeIfRequired(List<VersatileData> list) {
        for (VersatileData versatileData : list) {
            versatileData.time += this.timeShift;
            DateTime dateTime = new DateTime(versatileData.time).withZoneRetainFields(this.sourceTz);
            DateTime dateTime2 = dateTime.withZone(this.targetTz).toLocalDateTime().toDateTime();
            if (this.shiftHours != 0) {
                dateTime2 = dateTime2.plusHours(this.shiftHours);
            }
            if (this.minutesShift) {
                dateTime2 = dateTime2.plusMinutes(1);
            }
            versatileData.time = dateTime2.getMillis();
        }
    }

    private DownloadResultDto getForDay(long l) throws Exception {
        int n = SQTime.getFullYear((long)l);
        int n2 = SQTime.getMonthOriginal((long)l);
        DownloadResultDto downloadResultDto = this.dataCache.performLoad(this.tickerForDownload, n, n2, new DownloadMessageHandler(){

            @Override
            public void onDownloadMessage(String string, String string2) {
                DownloadEodStockHistorySymbolJob.this.progressListener.onError(string);
            }
        });
        return downloadResultDto;
    }

    private boolean evalDates() throws Exception {
        boolean bl = false;
        this.fromDate = this.aliasTicker != null ? this.aliasTicker.getDateFrom().getTime() : this.ticker.getDateFrom().getTime();
        this.toDate = this.aliasTicker != null ? this.aliasTicker.getDateTo().getTime() : this.ticker.getDateTo().getTime();
        long l = this.lastestDateFromFile = this.reader == null ? -1L : this.readOriginalFile();
        if (this.lastestDateFromFile > this.fromDate) {
            this.downloadFromDate = SQTime.addDays((long)this.lastestDateFromFile, (int)1);
            this.downloadFromDate = SQTime.correctDayStart((long)this.downloadFromDate);
        } else {
            this.downloadFromDate = this.fromDate;
        }
        if (this.lastestDateFromFile != -1L) {
            Date date = new Date(this.lastestDateFromFile);
            if (this.kind == TickerKind.FUTURES && (this.forceDownload || HistoryDataManager.get().shouldInvalidateFutureDatas(this.ticker.getTicker(), date))) {
                this.clearData();
                this.downloadFromDate = this.fromDate;
                bl = true;
            }
            if (this.kind == TickerKind.STOCK && (this.forceDownload || HistoryDataManager.get().shouldInvalidateStockDatas(this.ticker.getTicker(), date))) {
                this.clearData();
                this.downloadFromDate = this.fromDate;
                Log.debug("Performing full import of {}", (Object)this.ticker.getTicker());
                bl = true;
            }
        }
        this.totalDays = SQTime.getDaysBetween((long)this.downloadFromDate, (long)this.toDate) + 1;
        return bl;
    }

    private long readOriginalFile() throws Exception {
        long l = -1L;
        while (this.reader.readData()) {
            l = this.reader.tickData.time;
            VersatileData versatileData = this.createData(this.reader.tickData);
            this.writer.writeData(versatileData);
            this.storeStockVersatileDataToQueue(versatileData);
            ++this.totalRecords;
        }
        return l;
    }

    private void clearData() throws Exception {
        this.totalRecords = 0;
        this.datas.clear();
        if (this.writer != null) {
            this.writer.close();
            String string = DataManager.getDataFileName((String)"History", (String)this.symbol, (String)this.timeframe, (String)"No Session");
            this.writer = this.freeSymbol ? DataBinWriterNew.getInstance((int)1, (String)MainApp.getDataPath(), (InstrumentInfo)this.dataInfo.symbolInfo) : DataBinWriterNew.getCryptedInstance((int)1, (String)MainApp.getDataPath(), (InstrumentInfo)this.dataInfo.symbolInfo);
            this.writer.setFileName(string);
            this.writer.open();
        }
    }

    private void onError(String string) {
        this.progressListener.onError(string);
        this.closeFiles(false);
    }

    private void finish(long l) {
        try {
            if (this.downloadFromDate != -1L && l != -1L) {
                long l2 = this.timeframe.equals("D1") ? (long)(this.totalRecords * 60 * 60 * 24) : (long)(this.totalRecords * 60);
                DataManager.updateDataInBatch((String)"History", (String)this.symbol, (long)this.fromDate, (long)l, (int)this.totalRecords, (long)l2, (int)this.bartimeType, (String)this.timeframe, (String)this.dataInfo.timezone);
            }
        }
        catch (Exception exception) {
            Log.error("Error while saving results", (Throwable)exception);
            throw new RuntimeException(L.t((String)"Error while saving results", (Object[])new Object[0]));
        }
    }

    private void closeFiles(boolean bl) {
        try {
            this.writer.close();
        }
        catch (Exception exception) {
            // empty catch block
        }
        try {
            if (this.reader != null) {
                this.reader.closeFile();
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
        if (bl) {
            this.deleteCopyFile();
        } else {
            this.revertCopyFile();
        }
    }

    public boolean deleteCopyFile() {
        String string = DataManager.getDataFileName((String)"History", (String)this.symbol, (String)this.timeframe, (String)"No Session");
        String string2 = string + ".copy";
        return new File(string2).delete();
    }

    public void revertCopyFile() {
        String string = DataManager.getDataFileName((String)"History", (String)this.symbol, (String)this.timeframe, (String)"No Session");
        String string2 = string + ".copy";
        File file = new File(string2);
        if (!file.exists()) {
            return;
        }
        File file2 = new File(string);
        file2.delete();
        file.renameTo(file2);
    }
}

