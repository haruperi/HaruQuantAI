/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew
 *  com.strategyquant.datalib.timezone.Timezone
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  org.joda.time.DateTime
 *  org.joda.time.DateTimeZone
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.dukascopy;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.datalib.timezone.Timezone;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.dukascopy.DownloadResultDto;
import com.strategyquant.tradinglib.dukascopy.DukascopyUtils;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import java.io.ByteArrayInputStream;
import java.nio.ByteBuffer;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.Map;
import org.joda.time.DateTime;
import org.joda.time.DateTimeZone;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DukascopyBinaryMerger {
    public static final String DATE_TIME_FORMAT = "yyyy.MM.dd";
    public static final long VOLUME_CONST = 1000000L;
    private static final Logger Log = LoggerFactory.getLogger(DukascopyBinaryMerger.class);
    private Map<Integer, Long> dates = new HashMap<Integer, Long>();
    private LinkedList<VersatileData>[] queue;
    private String jobId;
    private int lastSavedHourIndex = -1;
    private ImportInfo importInfo;
    private int currentBatchSize;
    private boolean ignoreWeekend = false;
    private long realSavedPerBatch = 0L;
    private VersatileData origNotSavedTickData = new VersatileData();
    private DataBinWriterNew writer;
    private DataBinReaderNew reader;
    private DataManagerProgressListener progressListener;
    private int savedRows = 0;
    protected long requestFromDate;
    protected long fromDate = -1L;
    private long toDate = -1L;
    private int totalDays;
    protected volatile int performedDays = 0;
    private int lastEvaluatedDay = -1;
    private boolean stopped;
    private boolean skipProgress;
    private int lastSaved = -1;
    private long savedSecs = 0L;
    private String messagePrefix;
    private boolean saveError;
    private DateTimeZone sourceTz;
    private DateTimeZone targetTz;
    private int shiftHours = 0;

    public DukascopyBinaryMerger(String string, String string2, int n, ImportInfo importInfo) {
        this.jobId = string2;
        this.messagePrefix = string;
        this.importInfo = importInfo;
        this.totalDays = this.getTotalDays();
        this.requestFromDate = importInfo.oldDateFrom != 0L && importInfo.oldDateFrom < importInfo.dateFrom ? importInfo.oldDateFrom : importInfo.dateFrom;
        this.queue = new LinkedList[n];
        this.origNotSavedTickData.time = -1L;
    }

    public void setTargetTimezone(String string) {
        this.sourceTz = DateTimeZone.UTC;
        if (string.equals("EETUS")) {
            string = "America/New_York";
            this.shiftHours = 7;
        }
        this.targetTz = DateTimeZone.forID((String)Timezone.parseId((String)string));
    }

    public boolean isSaveError() {
        return this.saveError;
    }

    private int getTotalDays() {
        long l = this.importInfo.dateFrom;
        long l2 = this.importInfo.dateTo;
        if (this.importInfo.oldDateFrom != 0L && this.importInfo.oldDateFrom < l) {
            l = this.importInfo.oldDateFrom;
        }
        if (this.importInfo.oldDateTo != 0L && this.importInfo.oldDateTo > l2) {
            l2 = this.importInfo.oldDateTo;
        }
        return SQTime.getDaysBetween((long)l, (long)l2) + 1;
    }

    public void setIgnoreWeekend(boolean bl) {
        this.ignoreWeekend = bl;
    }

    public void resetWithBatchAndStart(int n, int n2) {
        this.lastSavedHourIndex = n;
        this.realSavedPerBatch = 0L;
        this.currentBatchSize = n2;
        for (int i = 0; i < this.queue.length; ++i) {
            this.queue[i] = null;
        }
    }

    public void reset(int n) {
        this.resetWithBatchAndStart(-1, n);
    }

    public int getJobsIndex(String string) {
        String string2 = string.substring(this.jobId.length() + 1);
        Integer n = Integer.parseInt(string2);
        return n;
    }

    private long getTime(int n, long l) {
        return l + (long)n;
    }

    private double getPrice(int n) {
        return this.importInfo.priceConstant * (double)n;
    }

    public void showError(long l, String string) {
        String string2 = String.format(this.messagePrefix + " %s", SQTime.toString((long)l, (String)DATE_TIME_FORMAT)) + " - " + L.t((String)"ERROR: %s", (Object[])new Object[]{string});
        this.evalPerformedDays(l);
        this.updateProgress(string2, false);
    }

    public synchronized void handleBi5Data(DownloadResultDto downloadResultDto, String string, boolean bl, boolean bl2) throws Exception {
        int n = this.getJobsIndex(string);
        long l = this.dates.get(n);
        if (!bl2 || downloadResultDto.getData() == null) {
            if (downloadResultDto.getErrorMessage() != null) {
                this.showError(l, "download failed: " + downloadResultDto.getErrorMessage());
            } else {
                this.showError(l, "download failed. Error code: " + downloadResultDto.getHttpCode());
            }
            return;
        }
        Log.debug("Decoding data");
        ByteBuffer byteBuffer = DukascopyUtils.decodeBi5Data(new ByteArrayInputStream(downloadResultDto.getData()));
        if (bl) {
            this.handleHourData(byteBuffer, n, l);
        } else {
            this.handleOhlcData(byteBuffer, n, l);
        }
        Log.debug("Decoding data finished");
        this.tryToSaveQueue(l);
    }

    private void handleHourData(ByteBuffer byteBuffer, int n, Long l) {
        boolean bl = false;
        if (byteBuffer != null) {
            while (byteBuffer.hasRemaining()) {
                VersatileData versatileData = new VersatileData();
                versatileData.time = this.getTime(byteBuffer.getInt(), l);
                versatileData.ask = this.getPrice(byteBuffer.getInt());
                versatileData.bid = this.getPrice(byteBuffer.getInt());
                byteBuffer.getFloat();
                versatileData.volume = byteBuffer.getFloat() * 1000000.0f;
                this.storeToQueue(n, versatileData);
                bl = true;
            }
        }
        if (!bl) {
            Log.debug("Data downloaded - but don't contains any tick data");
            this.storeToQueue(n, null);
        }
    }

    private void handleOhlcData(ByteBuffer byteBuffer, int n, Long l) {
        boolean bl = false;
        if (byteBuffer != null) {
            while (byteBuffer.hasRemaining()) {
                VersatileData versatileData = new VersatileData();
                int n2 = byteBuffer.getInt();
                versatileData.time = this.getTime(n2 * 1000, l);
                versatileData.open = this.getPrice(byteBuffer.getInt());
                versatileData.close = this.getPrice(byteBuffer.getInt());
                versatileData.low = this.getPrice(byteBuffer.getInt());
                versatileData.high = this.getPrice(byteBuffer.getInt());
                versatileData.volume = byteBuffer.getFloat() * 1000000.0f;
                this.storeToQueue(n, versatileData);
                bl = true;
            }
        }
        if (!bl) {
            Log.debug("Data downloaded - but doesn't contain any tick data");
            this.storeToQueue(n, null);
        }
    }

    public Long getDateForJob(String string) {
        int n = this.getJobsIndex(string);
        Long l = this.dates.get(n);
        return l;
    }

    public void tryToSaveQueue(long l) throws Exception {
        block4: {
            Log.debug("Trying to save datas in queue");
            int n = this.lastSavedHourIndex;
            while (true) {
                LinkedList<VersatileData> linkedList;
                if (++n == this.currentBatchSize) {
                    Log.debug("Everything saved");
                    if (this.realSavedPerBatch != 0L) break block4;
                    this.performedDays = SQTime.getDaysBetween((long)this.requestFromDate, (long)l);
                    linkedList = String.format(this.messagePrefix + " %s", SQTime.toString((long)l, (String)DATE_TIME_FORMAT));
                    this.updateProgress((String)((Object)linkedList), false);
                    break block4;
                }
                linkedList = this.queue[n];
                if (linkedList == null) break;
                long l2 = this.dates.get(n);
                Log.debug("Saving data for:" + this.getDateDesc(l2));
                for (VersatileData versatileData : linkedList) {
                    long l3;
                    if (this.importInfo.downloadM1Data && versatileData.volume > 0.0 && (l3 = Math.round(versatileData.volume * 100000.0)) == 0L) {
                        versatileData.volume = 1.0;
                    }
                    if (this.importInfo.downloadM1Data && !(versatileData.volume > 0.0)) continue;
                    this.performSave(versatileData, true);
                    ++this.realSavedPerBatch;
                }
                this.lastSavedHourIndex = n;
                this.queue[n] = null;
            }
            Log.debug("Skipping saving - found missing datas - waiting for them");
        }
    }

    public void storeToQueue(int n, VersatileData versatileData) {
        LinkedList<Object> linkedList = this.queue[n];
        if (linkedList == null) {
            this.queue[n] = linkedList = new LinkedList();
        }
        if (versatileData != null) {
            linkedList.add(versatileData);
        }
        if (this.importInfo.dateFrom == 0L) {
            this.importInfo.dateFrom = versatileData.time;
            this.totalDays = this.getTotalDays();
        }
    }

    public void register(int n, long l) {
        this.dates.put(n, l);
    }

    public long checkDate(long l) throws Exception {
        if (this.getReader() == null) {
            if (this.ignoreWeekend && SQTime.getDayOfWeek((long)l) == 6) {
                return SQTime.addDays((long)l, (int)1);
            }
            return l;
        }
        this.readTill(l, true);
        if (this.hasOrigNotSavedData()) {
            if (this.ignoreWeekend && SQTime.getDayOfWeek((long)l) == 6) {
                return SQTime.addDays((long)l, (int)1);
            }
            return l;
        }
        boolean bl = this.hasDaySomeRecords(l, !this.importInfo.overwrite);
        if (this.importInfo.overwrite || !bl) {
            return l;
        }
        long l2 = SQTime.addDays((long)l, (int)1);
        while ((bl = this.hasDaySomeRecords(l2, true)) || this.ignoreWeekend && SQTime.getDayOfWeek((long)l2) == 6) {
            l2 = SQTime.addDays((long)l2, (int)1);
        }
        return l2;
    }

    public void clearQueue(int n) {
        this.queue[n] = new LinkedList();
    }

    public void resetQueue(int n) {
        this.queue[n] = null;
    }

    public void setWriter(DataBinWriterNew dataBinWriterNew) {
        this.writer = dataBinWriterNew;
    }

    public void setReader(DataBinReaderNew dataBinReaderNew) {
        this.reader = dataBinReaderNew;
    }

    public void skipAllProgress() {
        this.skipProgress = true;
    }

    public void setStopped(boolean bl) {
        this.stopped = bl;
    }

    public long getFromDate() {
        return this.fromDate;
    }

    public long getToDate() {
        return this.toDate;
    }

    public int getSavedRows() {
        return this.savedRows;
    }

    public DataBinReaderNew getReader() {
        return this.reader;
    }

    protected boolean hasOrigNotSavedData() {
        return this.origNotSavedTickData.time == -1L;
    }

    public String getDateDesc(long l) {
        return SQTime.toString((long)l, (String)DATE_TIME_FORMAT);
    }

    public void setProgressListener(DataManagerProgressListener dataManagerProgressListener) {
        this.progressListener = dataManagerProgressListener;
    }

    public boolean readTill(long l, boolean bl) throws Exception {
        boolean bl2 = false;
        l = this.getRecountedTime(l);
        if (this.origNotSavedTickData.time != -1L) {
            if (this.origNotSavedTickData.time < l) {
                bl2 = true;
                if (bl) {
                    this.performSave(this.origNotSavedTickData, false);
                    this.setOrigNotSavedTickData(null);
                }
            } else {
                return false;
            }
        }
        if (this.reader != null) {
            while (this.reader.readData()) {
                this.setOrigNotSavedTickData(this.reader.tickData);
                if (this.origNotSavedTickData.time >= l) break;
                if (bl) {
                    this.performSave(this.origNotSavedTickData, false);
                    this.setOrigNotSavedTickData(null);
                }
                bl2 = true;
            }
            if (this.origNotSavedTickData.time < l && !bl) {
                this.setOrigNotSavedTickData(null);
            }
        }
        return bl2;
    }

    protected boolean hasDaySomeRecords(long l, boolean bl) throws Exception {
        long l2 = SQTime.addDays((long)l, (int)1);
        boolean bl2 = this.readTill(l2, bl);
        return bl2;
    }

    public long getSavedSecs() {
        return this.savedSecs;
    }

    public void performSave(VersatileData versatileData, boolean bl) throws Exception {
        try {
            this.saveError = false;
            this.recountTimeToTargetTz(versatileData, bl);
            this.writer.writeData(versatileData);
        }
        catch (Throwable throwable) {
            this.saveError = true;
        }
        ++this.savedRows;
        int n = SQTime.getDateTime((long)versatileData.time);
        if (this.lastSaved != n) {
            ++this.savedSecs;
        }
        this.lastSaved = n;
        long l = versatileData.time;
        if (l > this.toDate) {
            this.toDate = l;
        }
        if (l < this.fromDate || this.fromDate == -1L) {
            this.fromDate = l;
        }
        if (this.evalPerformedDays(versatileData.time)) {
            this.updateSaveProgress(versatileData.time);
        }
    }

    private void recountTimeToTargetTz(VersatileData versatileData, boolean bl) {
        if (!bl || this.targetTz == null) {
            return;
        }
        DateTime dateTime = new DateTime(versatileData.time).withZoneRetainFields(this.sourceTz);
        DateTime dateTime2 = dateTime.withZone(this.targetTz).toLocalDateTime().toDateTime();
        if (this.shiftHours != 0) {
            dateTime2 = dateTime2.plusHours(this.shiftHours);
        }
        versatileData.time = dateTime2.getMillis();
    }

    private long getRecountedTime(long l) {
        if (this.targetTz == null) {
            return l;
        }
        DateTime dateTime = new DateTime(l).withZoneRetainFields(this.sourceTz);
        DateTime dateTime2 = dateTime.withZone(this.targetTz).toLocalDateTime().toDateTime();
        if (this.shiftHours != 0) {
            dateTime2 = dateTime2.plusHours(this.shiftHours);
        }
        return dateTime2.getMillis();
    }

    private boolean evalPerformedDays(long l) {
        boolean bl;
        int n = SQTime.getDay((long)l);
        boolean bl2 = bl = n != this.lastEvaluatedDay;
        if (bl) {
            if (this.requestFromDate == 0L) {
                this.requestFromDate = l;
            }
            this.performedDays = SQTime.getDaysBetween((long)this.requestFromDate, (long)l);
            if (this.performedDays >= this.totalDays) {
                this.performedDays = this.totalDays - 1;
            }
        }
        this.lastEvaluatedDay = n;
        return bl;
    }

    public void updateProgress(String string, boolean bl) {
        if (this.progressListener != null && !this.skipProgress) {
            double d = SQUtils.round((double)((double)this.performedDays * 100.0 / (double)this.totalDays), (int)1);
            if (d < 100.0 || bl) {
                this.progressListener.onProgress(d);
            }
            if (this.stopped) {
                string = "Stopping - " + string;
            }
            this.progressListener.setMessage(string);
        }
    }

    public void updateSaveProgress(long l) {
        String string = String.format(this.messagePrefix + " %s", SQTime.toString((long)l, (String)DATE_TIME_FORMAT));
        this.updateProgress(string, false);
    }

    public void setFinishProgress(String string) {
        this.performedDays = this.totalDays;
        this.updateProgress(string, true);
    }

    public void setOrigNotSavedTickData(VersatileData versatileData) {
        if (versatileData == null) {
            this.origNotSavedTickData.time = -1L;
            return;
        }
        this.origNotSavedTickData.time = versatileData.time;
        this.origNotSavedTickData.volume = versatileData.volume;
        this.origNotSavedTickData.bid = versatileData.bid;
        this.origNotSavedTickData.ask = versatileData.ask;
        this.origNotSavedTickData.open = versatileData.open;
        this.origNotSavedTickData.close = versatileData.close;
        this.origNotSavedTickData.low = versatileData.low;
        this.origNotSavedTickData.high = versatileData.high;
    }

    public void finish() throws Exception {
        if (this.origNotSavedTickData.time != -1L) {
            this.performSave(this.origNotSavedTickData, false);
        }
        if (this.reader != null) {
            while (this.reader.readData()) {
                this.setOrigNotSavedTickData(this.reader.tickData);
                this.performSave(this.origNotSavedTickData, false);
            }
            this.setOrigNotSavedTickData(null);
        }
    }

    public long getRestDays() {
        return this.totalDays - this.performedDays;
    }

    public long getPerformedDays() {
        return this.performedDays;
    }
}

