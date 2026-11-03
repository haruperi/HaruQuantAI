/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.broker.BrokerDto
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.DateShifter
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew
 *  com.strategyquant.datalib.metatrader4.Mt4SymbolProperties
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.historyData.ICryptable
 *  com.strategyquant.lib.utils.IProgressListener
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.mt4;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.DateShifter;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew;
import com.strategyquant.datalib.metatrader4.Mt4SymbolProperties;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.historyData.ICryptable;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.tradinglib.project.websocket.WebSocketNotification;
import java.io.BufferedOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.Charset;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Mt4Exporter {
    private static final Logger LOG = LoggerFactory.getLogger(Mt4Exporter.class);
    private static final String COPYRIGHT = "(C)opyright 2003, MetaQuotes Software Corp.";
    private static final String[] TIMEFRAMES = new String[]{"M1", "M5", "M15", "M30", "H1", "H4", "D1"};
    private static final int[] TIMEFRAMES_INT = new int[]{1, 5, 15, 30, 60, 240, 1440};
    private static final int REFRESH_RATE = 10;
    private DataOutputStream[] outputsFxt = new DataOutputStream[TIMEFRAMES.length];
    private DataOutputStream[] outputsHst = new DataOutputStream[TIMEFRAMES.length];
    private long fromDate;
    private long toDate;
    private String sqSymbol;
    private String mt4Symbol;
    private int digits;
    private String dataFolder;
    private String serverName;
    private Mt4SymbolProperties properties;
    private volatile boolean canceled = false;
    private IProgressListener listener;
    private HstExporter hstExporter;
    private FxtExporter fxtExporter;
    private int[] extPeriodSeconds = new int[TIMEFRAMES.length];
    private int[] extBars = new int[TIMEFRAMES.length];
    private long[] extLastBarTime = new long[TIMEFRAMES.length];
    private double[] extLastOpen = new double[TIMEFRAMES.length];
    private double[] extLastLow = new double[TIMEFRAMES.length];
    private double[] extLastHigh = new double[TIMEFRAMES.length];
    private double[] extLastClose = new double[TIMEFRAMES.length];
    private int[] extLastVolume = new int[TIMEFRAMES.length];
    private long extLastTime;
    private long extStartTick;
    private long extEndTick;
    private long totalRecords;
    private volatile boolean paused;
    private DataBinReaderNew reader;
    private double tickSize;
    private String timeframe;
    private String baseCurrency;
    private String encoding;
    private boolean exportHst;
    private boolean exportFxt;
    private DateShifter dateShifter;
    private String targetTimezone;

    public Mt4Exporter(String string, String string2, String string3, long l, long l2, String string4, String string5, Mt4SymbolProperties mt4SymbolProperties, String string6, String string7, String string8, IProgressListener iProgressListener) {
        this.encoding = string3;
        this.sqSymbol = string;
        this.mt4Symbol = string2;
        this.fromDate = l;
        this.toDate = SQTime.addDays((long)l2, (int)1);
        this.properties = mt4SymbolProperties;
        this.dataFolder = string4;
        this.serverName = string5;
        this.timeframe = string6;
        this.targetTimezone = string8;
        this.listener = iProgressListener;
        this.exportHst = true;
        this.exportFxt = true;
        switch (string7) {
            case "hst": {
                this.exportFxt = false;
                break;
            }
            case "fxt": {
                this.exportHst = false;
            }
        }
        this.hstExporter = new HstExporter(this.exportHst);
        this.fxtExporter = new FxtExporter(this.exportFxt);
    }

    private void evalTimeZones(DataInfo dataInfo, String string) {
        String string2 = "UTC";
        if (dataInfo.brokerId != -1) {
            BrokerDto brokerDto = BrokerManager.getInstance().getBroker(Integer.valueOf(dataInfo.brokerId));
            string2 = brokerDto.getMtTimezone();
        }
        this.dateShifter = new DateShifter(string2, string);
    }

    public void export() throws IOException {
        try {
            LOG.info("Exporting MT4 symbol: " + this.mt4Symbol);
            this.canceled = false;
            for (int i = 0; i < TIMEFRAMES.length; ++i) {
                this.extPeriodSeconds[i] = TIMEFRAMES_INT[i] * 60 * 1000;
                this.extBars[i] = 0;
                this.extLastBarTime[i] = 0L;
            }
            this.extStartTick = 0L;
            this.extEndTick = 0L;
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)this.sqSymbol);
            this.evalTimeZones(dataInfo, this.targetTimezone);
            this.prepareReader();
            this.prepareWriters();
            this.performExport();
            this.closeWriters();
        }
        catch (Exception exception) {
            LOG.error("Error while exporting to MT4. Exc.", (Throwable)exception);
            this.listener.onError(exception.getMessage());
        }
    }

    private void prepareReader() throws Exception {
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)this.sqSymbol);
        this.reader = DataBinReaderNew.getInstance((int)2, (InstrumentInfo)dataInfo.symbolInfo);
        String string = DataManager.getDataFileName((String)"History", (String)this.sqSymbol, (String)"TICK", (String)"No Session");
        File file = new File(string);
        this.reader.setFileName(file.getAbsolutePath());
        this.reader.openFile();
        DataManager.checkDataExport((ICryptable)this.reader, (int)dataInfo.source);
        String string2 = dataInfo.uSymbol;
        if (string2 == null) {
            string2 = dataInfo.instrument;
        }
        this.baseCurrency = this.properties.exists("currency") ? this.properties.getStrValue("currency") : this.getBaseCurrency(string2);
        this.totalRecords = dataInfo.rows;
        this.digits = this.properties.exists("mode_digits") ? this.properties.getIntValue("mode_digits") : dataInfo.decimals;
        this.tickSize = dataInfo.symbolInfo.tickSize;
    }

    private String getBaseCurrency(String string) {
        if (string.length() >= 6) {
            return string.substring(string.length() - 3, string.length());
        }
        return string.substring(string.length() - 3);
    }

    private void performExport() throws Exception, IOException {
        long l = 0L;
        int n = 0;
        VersatileData versatileData = new VersatileData();
        while (this.reader.dataRemaining()) {
            int n2;
            boolean bl;
            this.reader.readData();
            versatileData = this.reader.tickData;
            versatileData.ask = SQUtils.round((double)versatileData.ask, (int)this.digits);
            versatileData.bid = SQUtils.round((double)versatileData.bid, (int)this.digits);
            this.dateShifter.transformToTimeZone(versatileData);
            l = versatileData.time;
            if (this.canceled) break;
            this.checkPaused();
            ++n;
            if (this.toDate > 0L && l >= this.toDate) break;
            boolean bl2 = bl = this.fromDate > 0L && l < this.fromDate;
            if (n % 10 != 0) {
                if (bl) {
                    this.listener.setMessage(L.t((String)"Export to MT4 - skipped %s", (Object[])new Object[]{SQTime.toDateMinuteString((long)l)}));
                } else {
                    this.listener.setMessage(L.t((String)"Exported to MT4 %s", (Object[])new Object[]{SQTime.toDateMinuteString((long)l)}));
                }
            }
            this.showProgress(n, false);
            if (bl) continue;
            this.extLastTime = versatileData.time;
            for (n2 = 0; n2 < TIMEFRAMES.length; ++n2) {
                long l2 = l / (long)this.extPeriodSeconds[n2];
                l2 *= (long)this.extPeriodSeconds[n2];
                boolean bl3 = false;
                if (n2 < 7) {
                    if (this.extLastBarTime[n2] != l2) {
                        bl3 = true;
                    }
                } else if (n2 == 7) {
                    if (l - this.extLastBarTime[n2] >= (long)this.extPeriodSeconds[n2]) {
                        bl3 = true;
                    }
                    if (bl3) {
                        l2 = l;
                        l2 -= l2 % 86400L;
                        while (SQTime.getDayOfWeekOriginal((long)l2) != 0) {
                            l2 -= 86400L;
                        }
                    }
                } else if (n2 == 8) {
                    if (this.extLastBarTime[n2] == 0L) {
                        bl3 = true;
                    }
                    if (SQTime.getDay((long)l) < 5 && l - this.extLastBarTime[n2] > 864000L) {
                        bl3 = true;
                    }
                    if (bl3) {
                        l2 = l;
                        l2 -= l2 % 86400L;
                        while (SQTime.getDay((long)l2) != 1) {
                            l2 -= 86400L;
                        }
                    }
                }
                if (bl3) {
                    if (this.extBars[n2] > 0) {
                        long l3;
                        this.hstExporter.writeBar(n2);
                        if (n2 == 0 && (l3 = (l2 - this.extLastBarTime[n2]) / (long)this.extPeriodSeconds[n2]) > 1L && l3 < 5L) {
                            long l4 = this.extLastBarTime[n2];
                            this.extLastLow[n2] = this.extLastClose[n2];
                            this.extLastHigh[n2] = this.extLastClose[n2];
                            this.extLastOpen[n2] = this.extLastClose[n2];
                            this.extLastVolume[n2] = 0;
                            int n3 = 1;
                            while ((long)n3 < l3) {
                                this.extLastBarTime[n2] = l4 + (long)(n3 * this.extPeriodSeconds[n2]);
                                this.hstExporter.writeBar(n2);
                                int n4 = n2;
                                this.extBars[n4] = this.extBars[n4] + 1;
                                ++n3;
                            }
                        }
                    }
                    this.extLastBarTime[n2] = l2;
                    this.extLastOpen[n2] = versatileData.bid;
                    this.extLastLow[n2] = versatileData.bid;
                    this.extLastHigh[n2] = versatileData.bid;
                    this.extLastClose[n2] = versatileData.bid;
                    this.extLastVolume[n2] = versatileData.volume > 0.0 ? (int)versatileData.volume : 1;
                    int n5 = n2;
                    this.extBars[n5] = this.extBars[n5] + 1;
                    continue;
                }
                if (this.extLastLow[n2] > versatileData.bid) {
                    this.extLastLow[n2] = versatileData.bid;
                }
                if (this.extLastHigh[n2] < versatileData.bid) {
                    this.extLastHigh[n2] = versatileData.bid;
                }
                this.extLastClose[n2] = versatileData.bid;
                int n6 = n2;
                this.extLastVolume[n6] = this.extLastVolume[n6] + (int)versatileData.volume;
            }
            if (this.extStartTick == 0L) {
                this.extStartTick = l;
            }
            this.extEndTick = l;
            n2 = this.computeSpread(versatileData.ask, versatileData.bid);
            this.fxtExporter.writeTick(n2);
            if (!this.isFxtTooBig(this.fxtExporter.saved)) continue;
            String string = String.format("Export to FXT finished, 4 GB file size limit reached. Data exported: %s - %s", SQTime.formatDate((long)this.extStartTick), SQTime.formatDate((long)this.extEndTick));
            WebSocketNotification.send("Metatrader 4 exporter", string, "SQMANAGER");
            break;
        }
    }

    private int computeSpread(double d, double d2) {
        double d3 = Math.abs(d2 - d);
        return (int)((d3 /= this.tickSize) * 10.0);
    }

    private boolean isFxtTooBig(long l) {
        return false;
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

    private void closeWriters() throws IOException {
        for (int i = 0; i < TIMEFRAMES.length; ++i) {
            if (this.skipTimeframe(i)) continue;
            this.hstExporter.writeBar(i);
            if (this.exportFxt) {
                this.outputsFxt[i].close();
            }
            if (this.exportHst) {
                this.outputsHst[i].close();
            }
            File file = this.getTargetFile(this.fxtExporter, i);
            this.fxtExporter.writeSummary(file, this.extBars[i]);
            this.fxtExporter.setReadOnly(file);
        }
    }

    private File getTargetFile(Exporter exporter, int n) {
        File file = new File(exporter.getPath());
        file.mkdirs();
        String string = exporter.getFileName(n);
        File file2 = new File(file, string);
        return file2;
    }

    private DataOutputStream getDataOutputStream(Exporter exporter, int n) throws FileNotFoundException {
        File file = this.getTargetFile(exporter, n);
        if (file.exists()) {
            file.setWritable(true);
        }
        DataOutputStream dataOutputStream = new DataOutputStream(new BufferedOutputStream(new FileOutputStream(file)));
        return dataOutputStream;
    }

    private boolean skipTimeframe(int n) {
        if (this.timeframe == null || this.timeframe.equalsIgnoreCase("All")) {
            return false;
        }
        String string = TIMEFRAMES[n];
        boolean bl = string.equalsIgnoreCase(this.timeframe);
        return !bl;
    }

    private void prepareWriters() throws IOException {
        for (int i = 0; i < TIMEFRAMES.length; ++i) {
            if (this.skipTimeframe(i)) continue;
            this.outputsFxt[i] = this.exportFxt ? this.getDataOutputStream(this.fxtExporter, i) : null;
            this.fxtExporter.writeHeader(this.outputsFxt[i], i);
            this.outputsHst[i] = this.exportHst ? this.getDataOutputStream(this.hstExporter, i) : null;
            this.hstExporter.writeHeader(this.outputsHst[i], i);
        }
    }

    public boolean isCanceled() {
        return this.canceled;
    }

    public void showProgress(double d, boolean bl) {
        double d2 = SQUtils.round((double)(d * 100.0 / (double)this.totalRecords), (int)1);
        if (d2 < 1.0) {
            d2 = 1.0;
        }
        if (d2 < 100.0 || bl) {
            this.listener.onProgress(d2);
        }
    }

    public void cancel() {
        this.canceled = true;
    }

    private byte[] getBytes(String string, int n, String string2) {
        byte[] byArray;
        byte[] byArray2 = new byte[n];
        if (string.length() > n) {
            string = string.substring(0, n - 1);
        }
        if (string2 != null && !string2.isBlank()) {
            Charset charset = null;
            try {
                charset = Charset.forName(string2);
            }
            catch (Exception exception) {
                LOG.error("", (Throwable)exception);
                throw new RuntimeException("Invalid encoding: " + string2);
            }
            byArray = string.getBytes(charset);
        } else {
            byArray = string.getBytes();
        }
        for (int i = 0; i < byArray.length; ++i) {
            byArray2[i] = byArray[i];
        }
        return byArray2;
    }

    private void writeString(DataOutputStream dataOutputStream, String string, int n) throws IOException {
        dataOutputStream.write(this.getBytes(string, n, null));
    }

    private void writeString(DataOutputStream dataOutputStream, String string, int n, String string2) throws IOException {
        dataOutputStream.write(this.getBytes(string, n, string2));
    }

    private void writeLong(DataOutputStream dataOutputStream, long l) throws IOException {
        ByteBuffer byteBuffer = ByteBuffer.allocate(8);
        byteBuffer.order(ByteOrder.LITTLE_ENDIAN);
        byteBuffer.putLong(l);
        dataOutputStream.write(byteBuffer.array());
    }

    private void writeInt(DataOutputStream dataOutputStream, int n) throws IOException {
        dataOutputStream.write(this.getIntBytes(n));
    }

    private void writeIntArray(DataOutputStream dataOutputStream, int[] nArray) throws IOException {
        for (int n : nArray) {
            this.writeInt(dataOutputStream, n);
        }
    }

    private void writeTimestamp(DataOutputStream dataOutputStream, long l) throws IOException {
        dataOutputStream.write(this.getIntBytesFromTimestamp(l));
    }

    private byte[] getIntBytesFromTimestamp(long l) {
        ByteBuffer byteBuffer = ByteBuffer.allocate(4);
        byteBuffer.order(ByteOrder.LITTLE_ENDIAN);
        int n = (int)(l /= 1000L);
        byteBuffer.putInt(n);
        return byteBuffer.array();
    }

    private byte[] getIntBytes(int n) {
        ByteBuffer byteBuffer = ByteBuffer.allocate(4);
        byteBuffer.order(ByteOrder.LITTLE_ENDIAN);
        byteBuffer.putInt(n);
        return byteBuffer.array();
    }

    private void writeDouble(DataOutputStream dataOutputStream, double d) throws IOException {
        ByteBuffer byteBuffer = ByteBuffer.allocate(8);
        byteBuffer.order(ByteOrder.LITTLE_ENDIAN);
        byteBuffer.putDouble(d);
        dataOutputStream.write(byteBuffer.array());
    }

    public void pause() {
        this.paused = true;
    }

    public void restart() {
        this.paused = false;
    }

    private class HstExporter
    implements Exporter {
        private static final int HST_VERSION = 401;
        private boolean export;

        public HstExporter(boolean bl) {
            this.export = bl;
        }

        public void writeBar(int n) throws IOException {
            if (!this.export) {
                return;
            }
            if (Mt4Exporter.this.skipTimeframe(n)) {
                return;
            }
            DataOutputStream dataOutputStream = Mt4Exporter.this.outputsHst[n];
            Mt4Exporter.this.writeTimestamp(dataOutputStream, Mt4Exporter.this.extLastBarTime[n]);
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            Mt4Exporter.this.writeDouble(dataOutputStream, Mt4Exporter.this.extLastOpen[n]);
            Mt4Exporter.this.writeDouble(dataOutputStream, Mt4Exporter.this.extLastHigh[n]);
            Mt4Exporter.this.writeDouble(dataOutputStream, Mt4Exporter.this.extLastLow[n]);
            Mt4Exporter.this.writeDouble(dataOutputStream, Mt4Exporter.this.extLastClose[n]);
            Mt4Exporter.this.writeLong(dataOutputStream, Math.max(1L, (long)Mt4Exporter.this.extLastVolume[n]));
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            Mt4Exporter.this.writeLong(dataOutputStream, Mt4Exporter.this.extLastVolume[n]);
        }

        @Override
        public String getFileName(int n) {
            return Mt4Exporter.this.mt4Symbol + TIMEFRAMES_INT[n] + ".hst";
        }

        @Override
        public void writeHeader(DataOutputStream dataOutputStream, int n) throws IOException {
            if (!this.export) {
                return;
            }
            Mt4Exporter.this.writeInt(dataOutputStream, 401);
            Mt4Exporter.this.writeString(dataOutputStream, Mt4Exporter.COPYRIGHT, 64);
            Mt4Exporter.this.writeString(dataOutputStream, Mt4Exporter.this.mt4Symbol, 12, Mt4Exporter.this.encoding);
            Mt4Exporter.this.writeInt(dataOutputStream, TIMEFRAMES_INT[n]);
            Mt4Exporter.this.writeInt(dataOutputStream, Mt4Exporter.this.digits);
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            dataOutputStream.write(new byte[52]);
        }

        @Override
        public String getPath() {
            return Mt4Exporter.this.dataFolder + "//history//" + Mt4Exporter.this.serverName;
        }
    }

    private class FxtExporter
    implements Exporter {
        private static final int FXT_HEADER_SIZE = 728;
        private static final int FXT_RECORD_SIZE = 56;
        private static final String FXT_COPYRIGHT = "(C)opyright 2005-2007, MetaQuotes Software Corp.";
        private static final int FXT_LEVERAGE = 100;
        private static final double FXT_COMM_BASE = 0.0;
        private static final int SWAP_ROLLOVER3DAYS = 3;
        private static final int FXT_SWAP_ENABLE = 1;
        private static final int FXT_GTC_PENDINGS = 0;
        private static final double FXT_MODEL_QUALITY = 68.0;
        private static final int FXT_BARS = 0;
        private static final int FXT_MODEL = 0;
        private static final int FXT_VERSION = 405;
        private static final int COMM_TYPE_PIPS = 1;
        private static final int COMMISSION_PER_LOT = 0;
        private static final int FXT_FROM = 0;
        private static final int FXT_TO = 0;
        private static final int MARGIN_CALC_FOREX = 0;
        private static final int MARGIN_CALC_CFD = 1;
        private static final int MARGIN_CALC_FUTURES = 2;
        private static final int MARGIN_CALC_CFDINDEX = 3;
        private static final int MARGIN_CALC_CFDLEVERAGE = 4;
        private long saved = 0L;
        private boolean export;

        public FxtExporter(boolean bl) {
            this.export = bl;
        }

        public void writeTick(int n) throws IOException {
            if (!this.export) {
                return;
            }
            for (int i = 0; i < TIMEFRAMES.length; ++i) {
                if (Mt4Exporter.this.skipTimeframe(i)) continue;
                Mt4Exporter.this.writeLong(Mt4Exporter.this.outputsFxt[i], Mt4Exporter.this.extLastBarTime[i] / 1000L);
                Mt4Exporter.this.writeDouble(Mt4Exporter.this.outputsFxt[i], Mt4Exporter.this.extLastOpen[i]);
                Mt4Exporter.this.writeDouble(Mt4Exporter.this.outputsFxt[i], Mt4Exporter.this.extLastHigh[i]);
                Mt4Exporter.this.writeDouble(Mt4Exporter.this.outputsFxt[i], Mt4Exporter.this.extLastLow[i]);
                Mt4Exporter.this.writeDouble(Mt4Exporter.this.outputsFxt[i], Mt4Exporter.this.extLastClose[i]);
                Mt4Exporter.this.writeInt(Mt4Exporter.this.outputsFxt[i], Math.max(1, Mt4Exporter.this.extLastVolume[i]));
                Mt4Exporter.this.writeInt(Mt4Exporter.this.outputsFxt[i], n);
                Mt4Exporter.this.writeTimestamp(Mt4Exporter.this.outputsFxt[i], Mt4Exporter.this.extLastTime);
                Mt4Exporter.this.writeInt(Mt4Exporter.this.outputsFxt[i], 4);
            }
            this.saved += 56L;
        }

        @Override
        public String getFileName(int n) {
            return Mt4Exporter.this.mt4Symbol + TIMEFRAMES_INT[n] + "_0.fxt";
        }

        @Override
        public void writeHeader(DataOutputStream dataOutputStream, int n) throws IOException {
            if (!this.export) {
                return;
            }
            Mt4Exporter.this.writeInt(dataOutputStream, 405);
            Mt4Exporter.this.writeString(dataOutputStream, FXT_COPYRIGHT, 64);
            Mt4Exporter.this.writeString(dataOutputStream, Mt4Exporter.this.serverName, 128);
            Mt4Exporter.this.writeString(dataOutputStream, Mt4Exporter.this.mt4Symbol, 12, Mt4Exporter.this.encoding);
            Mt4Exporter.this.writeInt(dataOutputStream, TIMEFRAMES_INT[n]);
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            Mt4Exporter.this.writeTimestamp(dataOutputStream, Mt4Exporter.this.fromDate);
            Mt4Exporter.this.writeTimestamp(dataOutputStream, Mt4Exporter.this.toDate);
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            Mt4Exporter.this.writeDouble(dataOutputStream, 68.0);
            Mt4Exporter.this.writeString(dataOutputStream, Mt4Exporter.this.baseCurrency, 12);
            int n2 = Mt4Exporter.this.properties.getIntValue("spread");
            Mt4Exporter.this.writeInt(dataOutputStream, n2);
            Mt4Exporter.this.writeInt(dataOutputStream, Mt4Exporter.this.digits);
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            double d = Mt4Exporter.this.properties.getDoubleValue("mode_point");
            if (d == 0.0) {
                d = 1.0E-5;
            }
            Mt4Exporter.this.writeDouble(dataOutputStream, d);
            double d2 = Mt4Exporter.this.properties.getDoubleValue("lot_min");
            Mt4Exporter.this.writeInt(dataOutputStream, (int)(d2 * 100.0));
            double d3 = Mt4Exporter.this.properties.getDoubleValue("lot_max");
            Mt4Exporter.this.writeInt(dataOutputStream, (int)(d3 * 100.0));
            double d4 = Mt4Exporter.this.properties.getDoubleValue("lot_step");
            Mt4Exporter.this.writeInt(dataOutputStream, (int)(d4 * 100.0));
            int n3 = Mt4Exporter.this.properties.getIntValue("stops_level");
            Mt4Exporter.this.writeInt(dataOutputStream, n3);
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            double d5 = Mt4Exporter.this.properties.getDoubleValue("contract_size");
            Mt4Exporter.this.writeDouble(dataOutputStream, d5);
            double d6 = Mt4Exporter.this.properties.getDoubleValue("tick_value");
            Mt4Exporter.this.writeDouble(dataOutputStream, d6);
            double d7 = Mt4Exporter.this.properties.getDoubleValue("tick_size");
            Mt4Exporter.this.writeDouble(dataOutputStream, d7);
            int n4 = Mt4Exporter.this.properties.getIntValue("profit_mode");
            Mt4Exporter.this.writeInt(dataOutputStream, n4);
            Mt4Exporter.this.writeInt(dataOutputStream, 1);
            Mt4Exporter.this.writeInt(dataOutputStream, Mt4Exporter.this.properties.getIntValue("swap_type"));
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            Mt4Exporter.this.writeDouble(dataOutputStream, Mt4Exporter.this.properties.getDoubleValue("swap_long"));
            Mt4Exporter.this.writeDouble(dataOutputStream, Mt4Exporter.this.properties.getDoubleValue("swap_short"));
            Mt4Exporter.this.writeInt(dataOutputStream, 3);
            Mt4Exporter.this.writeInt(dataOutputStream, 100);
            Mt4Exporter.this.writeInt(dataOutputStream, Mt4Exporter.this.properties.getIntValue("free_margin_mode"));
            Mt4Exporter.this.writeInt(dataOutputStream, Mt4Exporter.this.properties.getIntValue("margin_mode"));
            Mt4Exporter.this.writeInt(dataOutputStream, Mt4Exporter.this.properties.getIntValue("margin_stopout"));
            Mt4Exporter.this.writeInt(dataOutputStream, Mt4Exporter.this.properties.getIntValue("margin_stopout_mode"));
            Mt4Exporter.this.writeDouble(dataOutputStream, Mt4Exporter.this.properties.getDoubleValue("margin_initial"));
            Mt4Exporter.this.writeDouble(dataOutputStream, Mt4Exporter.this.properties.getDoubleValue("margin_maintenance"));
            Mt4Exporter.this.writeDouble(dataOutputStream, Mt4Exporter.this.properties.getDoubleValue("margin_hedged"));
            int n5 = Mt4Exporter.this.properties.getIntValue("mode_margincalcmode");
            double d8 = 0.0;
            String string = "";
            double d9 = 1.0;
            switch (n5) {
                case 1: 
                case 2: 
                case 3: 
                case 4: {
                    string = "USD";
                    d8 = Mt4Exporter.this.properties.getDoubleValue("mode_bid") * d5 / Mt4Exporter.this.properties.getDoubleValue("mode_marginrequired");
                    if (!(d8 < 0.97) && !(d8 > 1.03)) break;
                    d9 = Math.floor(d8);
                    break;
                }
                case 0: {
                    d9 = 1.0;
                    string = Mt4Exporter.this.baseCurrency;
                }
            }
            Mt4Exporter.this.writeDouble(dataOutputStream, d9);
            Mt4Exporter.this.writeString(dataOutputStream, string, 12);
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            Mt4Exporter.this.writeDouble(dataOutputStream, 0.0);
            Mt4Exporter.this.writeInt(dataOutputStream, 1);
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            int[] nArray = new int[6];
            nArray[0] = 1;
            Mt4Exporter.this.writeIntArray(dataOutputStream, nArray);
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            Mt4Exporter.this.writeInt(dataOutputStream, 0);
            Mt4Exporter.this.writeInt(dataOutputStream, Mt4Exporter.this.properties.getIntValue("freeze_level"));
            dataOutputStream.write(new byte[244]);
            this.saved = 728L;
        }

        @Override
        public String getPath() {
            return Mt4Exporter.this.dataFolder + "//tester//history";
        }

        public void setReadOnly(File file) {
            if (!this.export) {
                return;
            }
            file.setReadOnly();
        }

        public void writeSummary(File file, int n) throws IOException {
            if (!this.export) {
                return;
            }
            RandomAccessFile randomAccessFile = new RandomAccessFile(file, "rw");
            randomAccessFile.seek(216L);
            randomAccessFile.write(Mt4Exporter.this.getIntBytes(n));
            randomAccessFile.write(Mt4Exporter.this.getIntBytesFromTimestamp(Mt4Exporter.this.extStartTick));
            randomAccessFile.write(Mt4Exporter.this.getIntBytesFromTimestamp(Mt4Exporter.this.extEndTick));
            randomAccessFile.close();
        }
    }

    private static interface Exporter {
        public String getFileName(int var1);

        public void writeHeader(DataOutputStream var1, int var2) throws IOException;

        public String getPath();
    }
}

