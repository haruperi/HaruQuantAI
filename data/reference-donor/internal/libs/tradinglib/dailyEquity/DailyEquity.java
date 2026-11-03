/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  it.unimi.dsi.fastutil.longs.Long2FloatMap$Entry
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 *  it.unimi.dsi.fastutil.longs.LongBidirectionalIterator
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.dailyEquity;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.Result;
import it.unimi.dsi.fastutil.longs.Long2FloatMap;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;
import it.unimi.dsi.fastutil.longs.LongBidirectionalIterator;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutput;
import java.io.PrintWriter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DailyEquity {
    private static final Logger Log = LoggerFactory.getLogger((String)"DailyEquitySaver");
    private static final String valueDelimiter = ";";
    private static final String lineDelimiter = "\n";

    public static File createTempFileOldUnused(Result result) {
        Long2FloatRBTreeMap long2FloatRBTreeMap = result.getWorstDailyEquity();
        if (long2FloatRBTreeMap == null) {
            return null;
        }
        PrintWriter printWriter = null;
        String string = MainApp.getDataPath() + "/internal/tmp/dailyEquity";
        SQUtils.ensureDirExists((String)string);
        try {
            File file = File.createTempFile("sq4-dailyEquity-", ".csv", new File(string));
            printWriter = new PrintWriter(file);
            LongBidirectionalIterator longBidirectionalIterator = long2FloatRBTreeMap.keySet().iterator();
            while (longBidirectionalIterator.hasNext()) {
                long l = (Long)longBidirectionalIterator.next();
                double d = long2FloatRBTreeMap.get(l);
                printWriter.print(l + valueDelimiter + d + lineDelimiter);
            }
            printWriter.flush();
            printWriter.close();
            return file;
        }
        catch (Exception exception) {
            if (printWriter != null) {
                printWriter.close();
            }
            Log.error("Writing daily equity values to file '" + string + "' failed. ", (Throwable)exception);
            return null;
        }
    }

    public static void loadCsv(Result result, InputStream inputStream) {
        try {
            String string = SQUtils.inputStreamToString((InputStream)inputStream);
            String[] stringArray = string.split(lineDelimiter);
            Long2FloatRBTreeMap long2FloatRBTreeMap = new Long2FloatRBTreeMap();
            for (int i = 0; i < stringArray.length; ++i) {
                String string2 = stringArray[i];
                String[] stringArray2 = string2.split(valueDelimiter);
                if (stringArray2.length != 2) continue;
                long2FloatRBTreeMap.addTo(Long.parseLong(stringArray2[0]), (float)Double.parseDouble(stringArray2[1]));
            }
            result.setWorstDailyEquity(long2FloatRBTreeMap);
        }
        catch (Exception exception) {
            Log.error("Reading daily equity values of result '" + result.getResultKey() + "' failed. ", (Throwable)exception);
        }
    }

    public static void serialize(Result result, ObjectOutput objectOutput) {
        Long2FloatRBTreeMap long2FloatRBTreeMap = result.getWorstDailyEquity();
        try {
            objectOutput.writeInt(long2FloatRBTreeMap == null ? 0 : long2FloatRBTreeMap.size());
            if (long2FloatRBTreeMap == null) {
                return;
            }
            for (Long2FloatMap.Entry entry : long2FloatRBTreeMap.long2FloatEntrySet()) {
                long l = entry.getLongKey();
                double d = entry.getFloatValue();
                objectOutput.writeLong(l);
                objectOutput.writeDouble(d);
            }
        }
        catch (Exception exception) {
            Log.error("Writing daily equity values to binary file failed. ", (Throwable)exception);
        }
        try {
            objectOutput.flush();
        }
        catch (IOException iOException) {
            Log.error("Error flushing", (Throwable)iOException);
        }
    }

    public static void load(Result result, InputStream inputStream) {
        try {
            ObjectInputStream objectInputStream = new ObjectInputStream(inputStream);
            int n = objectInputStream.readInt();
            if (n == 0) {
                return;
            }
            Long2FloatRBTreeMap long2FloatRBTreeMap = new Long2FloatRBTreeMap();
            for (int i = 0; i < n; ++i) {
                long l = objectInputStream.readLong();
                double d = objectInputStream.readDouble();
                long2FloatRBTreeMap.addTo(l, (float)d);
            }
            result.setWorstDailyEquity(long2FloatRBTreeMap);
            objectInputStream.close();
        }
        catch (Exception exception) {
            Log.error("Reading daily equity values of result '" + result.getResultKey() + "' failed. ", (Throwable)exception);
        }
    }
}

