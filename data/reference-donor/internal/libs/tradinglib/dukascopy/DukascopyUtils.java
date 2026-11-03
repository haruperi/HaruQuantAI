/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  SevenZip.Compression.LZMA.Decoder
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.utils.Pair
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.dukascopy;

import SevenZip.Compression.LZMA.Decoder;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.utils.Pair;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DukascopyUtils {
    public static final Logger Log = LoggerFactory.getLogger(DukascopyUtils.class);
    private static Decoder decoder = new Decoder();

    public static synchronized ByteBuffer decodeBi5Data(InputStream inputStream) {
        try {
            ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
            long l = 0L;
            int n = 5;
            byte[] byArray = new byte[n];
            if (inputStream.read(byArray, 0, n) != n) {
                return null;
            }
            if (!decoder.SetDecoderProperties(byArray)) {
                throw new Exception(L.t((String)"Incorrect stream properties", (Object[])new Object[0]));
            }
            for (int i = 0; i < 8; ++i) {
                int n2 = inputStream.read();
                if (n2 < 0) {
                    throw new Exception(L.t((String)"Can't read stream size", (Object[])new Object[0]));
                }
                l |= (long)n2 << 8 * i;
            }
            if (!decoder.Code(inputStream, (OutputStream)byteArrayOutputStream, l)) {
                throw new Exception(L.t((String)"Error in data stream", (Object[])new Object[0]));
            }
            byte[] byArray2 = byteArrayOutputStream.toByteArray();
            return ByteBuffer.wrap(byArray2);
        }
        catch (Exception exception) {
            Log.error("Failed to decode .bi5 data. Exc.", (Throwable)exception);
            throw new RuntimeException(L.t((String)"Failed to decode .bi5 data. Exc.", (Object[])new Object[0]), exception);
        }
    }

    public static boolean deleteCopyFile(String string, String string2) {
        String string3 = DataManager.getDataFileName((String)"History", (String)string, (String)string2, (String)"No Session");
        String string4 = string3 + ".copy";
        return new File(string4).delete();
    }

    public static void revertCopyFile(String string, String string2) {
        String string3 = DataManager.getDataFileName((String)"History", (String)string, (String)string2, (String)"No Session");
        String string4 = string3 + ".copy";
        File file = new File(string4);
        if (!file.exists()) {
            return;
        }
        File file2 = new File(string3);
        file2.delete();
        file.renameTo(file2);
    }

    public static Pair<DataBinReaderNew, DataBinWriterNew> prepareFiles(ImportInfo importInfo, String string) throws Exception {
        DataBinWriterNew dataBinWriterNew;
        String string2 = DataManager.getDataFileName((String)"History", (String)importInfo.symbol, (String)string, (String)"No Session");
        String string3 = string2 + ".copy";
        File file = new File(string2);
        File file2 = new File(string3);
        int n = string.equals("TICK") ? 2 : 1;
        DataBinReaderNew dataBinReaderNew = null;
        if (file.exists()) {
            if (file.length() == 0L) {
                file.delete();
            } else {
                try {
                    Files.copy(file.toPath(), file2.toPath(), StandardCopyOption.REPLACE_EXISTING);
                    dataBinReaderNew = DataBinReaderNew.getInstance((int)n, (InstrumentInfo)importInfo.instrumentInfo);
                    dataBinReaderNew.setFileName(string3);
                    dataBinReaderNew.openFile();
                }
                catch (Exception exception) {
                    Log.error("Cannot make a copy of existing symbol data file. ", (Throwable)exception);
                    throw new Exception(L.t((String)"Error - Cannot make a copy of existing symbol data file.", (Object[])new Object[0]), exception);
                }
            }
        }
        try {
            dataBinWriterNew = DataBinWriterNew.getInstance((int)n, (String)MainApp.getDataPath(), (InstrumentInfo)importInfo.instrumentInfo);
            dataBinWriterNew.setFileName(string2);
            dataBinWriterNew.open();
        }
        catch (Exception exception) {
            Log.error("Cannot open symbol data file for writing. ", (Throwable)exception);
            throw new Exception(L.t((String)"Error - Cannot open symbol data file for writing.", (Object[])new Object[0]));
        }
        return new Pair(dataBinReaderNew, (Object)dataBinWriterNew);
    }

    public static String generateCdnYearUrl(String string, int n, String string2) {
        return string + "/" + string2 + "/" + n + ".zip";
    }

    public static String generateCdnMonthUrl(String string, int n, int n2, String string2) {
        String string3 = String.format("%d_%02d", n, n2);
        return string + "/" + string2 + "/" + string3 + ".zip";
    }

    public static String generateTickDukascopyUrl(long l, String string) {
        int n = SQTime.getFullYear((long)l);
        int n2 = SQTime.getMonth((long)l);
        int n3 = SQTime.getDay((long)l);
        int n4 = SQTime.getHour((long)l);
        String string2 = String.format("%d/%02d/%02d/%02d", n, n2, n3, n4);
        return "http://datafeed.dukascopy.com/datafeed/" + string + "/" + string2 + "h_ticks.bi5";
    }

    public static String generateM1DukascopyUrl(long l, String string) {
        int n = SQTime.getFullYear((long)l);
        int n2 = SQTime.getMonth((long)l);
        int n3 = SQTime.getDay((long)l);
        String string2 = String.format("%d/%02d/%02d", n, n2, n3);
        return "https://datafeed.dukascopy.com/datafeed/" + string + "/" + string2 + "/BID_candles_min_1.bi5";
    }
}

