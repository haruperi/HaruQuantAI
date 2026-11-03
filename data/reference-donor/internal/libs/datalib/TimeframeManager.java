/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.constants.SQPaths
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.timeframe.TimeframesComparator;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.constants.SQPaths;
import java.io.File;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TimeframeManager {
    public static final Logger Log = LoggerFactory.getLogger(TimeframeManager.class);
    public static final String TF_UNKNOWN = "unknown";
    public static final String TF_INTRADAY = "Intraday";
    public static final int TF_INT_UNKNOWN = -2;
    public static final String TF_TICK = "TICK";
    public static final String TF_M1 = "M1";
    public static final String TF_M3 = "M3";
    public static final String TF_M5 = "M5";
    public static final String TF_M15 = "M15";
    public static final String TF_M30 = "M30";
    public static final String TF_H1 = "H1";
    public static final String TF_H2 = "H2";
    public static final String TF_H3 = "H3";
    public static final String TF_H4 = "H4";
    public static final String TF_H6 = "H6";
    public static final String TF_H8 = "H8";
    public static final String TF_H12 = "H12";
    public static final String TF_D1 = "D1";
    public static final String TF_WEEKLY = "Weekly";
    public static final String TF_MONTHLY = "Monthly";
    private static final long MINUTE_MILLIS = 60000L;
    private static final long HOUR_MILLIS = 3600000L;
    private static final long DAY_MILLIS = 86400000L;
    private static final long WEEK_MILLIS = 604800000L;
    private static final long MONTH_MILLIS = 2419200000L;
    public static final int PRECISION_SELECTED_TF = 1;
    public static final int PRECISION_BASE_TF = 2;
    public static String filePath = SQPaths.settingsDirPath + "/customTimeframes.txt";
    private static final String delimiter = "\r\n";
    private ArrayList<String> defaultTimeframes = new ArrayList();
    private ArrayList<String> customTimeframes = new ArrayList();
    private static TimeframeManager instance;

    public static synchronized TimeframeManager getInstance() {
        if (instance == null) {
            instance = new TimeframeManager();
        }
        return instance;
    }

    private TimeframeManager() {
        this.defaultTimeframes.clear();
        this.defaultTimeframes.add(TF_TICK);
        this.defaultTimeframes.add(TF_M1);
        this.defaultTimeframes.add(TF_M5);
        this.defaultTimeframes.add(TF_M15);
        this.defaultTimeframes.add(TF_M30);
        this.defaultTimeframes.add(TF_H1);
        this.defaultTimeframes.add(TF_H4);
        this.defaultTimeframes.add(TF_D1);
        this.defaultTimeframes.add(TF_WEEKLY);
        this.defaultTimeframes.add(TF_MONTHLY);
        File file = new File(filePath);
        if (file.exists()) {
            try {
                SQUtils.fileToArrayList(this.customTimeframes, (String)filePath, (String)delimiter);
                while (this.customTimeframes.contains("")) {
                    this.customTimeframes.remove("");
                }
            }
            catch (Exception exception) {
                Log.error("Cannot load custom timeframes file. ", (Throwable)exception);
            }
        } else {
            Log.warn("Custom timeframes file doesn't exist.");
        }
    }

    private boolean isValid(String string) {
        if (string == null || string.isEmpty()) {
            return false;
        }
        if (string.equals(TF_MONTHLY)) {
            return true;
        }
        if (string.equals(TF_WEEKLY)) {
            return true;
        }
        if (string.startsWith("S") || string.startsWith("M") || string.startsWith("H") || string.startsWith("D")) {
            try {
                Integer.parseInt(string.substring(1));
                return true;
            }
            catch (Exception exception) {
                return false;
            }
        }
        return false;
    }

    public static ArrayList<String> getTimeframes() {
        return TimeframeManager.getInstance()._getTimeframes();
    }

    public static ArrayList<String> getPredefinedTimeframes() {
        ArrayList<String> arrayList = new ArrayList<String>();
        arrayList.add(TF_TICK);
        arrayList.add(TF_M1);
        arrayList.add(TF_M3);
        arrayList.add(TF_M5);
        arrayList.add(TF_M15);
        arrayList.add(TF_M30);
        arrayList.add(TF_H1);
        arrayList.add(TF_H2);
        arrayList.add(TF_H3);
        arrayList.add(TF_H4);
        arrayList.add(TF_H6);
        arrayList.add(TF_H8);
        arrayList.add(TF_H12);
        arrayList.add(TF_D1);
        arrayList.add(TF_WEEKLY);
        arrayList.add(TF_MONTHLY);
        return arrayList;
    }

    public static void addTimeframe(String string) throws Exception {
        TimeframeManager.getInstance()._addTimeframe(string);
    }

    public static String translateSQ3TFToString(int n) {
        switch (n) {
            case 0: {
                return TF_TICK;
            }
            case 1: {
                return TF_M1;
            }
            case 5: {
                return TF_M5;
            }
            case 14: {
                return "M14";
            }
            case 15: {
                return TF_M15;
            }
            case 30: {
                return TF_M30;
            }
            case 53: {
                return "M53";
            }
            case 60: {
                return TF_H1;
            }
            case 120: {
                return TF_H2;
            }
            case 240: {
                return TF_H4;
            }
            case 1440: {
                return TF_D1;
            }
            case 10080: {
                return TF_WEEKLY;
            }
            case 43200: {
                return TF_MONTHLY;
            }
            case -2: {
                return TF_UNKNOWN;
            }
            case -10: {
                return TF_INTRADAY;
            }
        }
        return TF_UNKNOWN;
    }

    public static int translateToMTConstant(String string) {
        switch (string) {
            case "TICK": {
                return 0;
            }
            case "M1": {
                return 1;
            }
            case "M5": {
                return 5;
            }
            case "M14": {
                return 14;
            }
            case "M15": {
                return 15;
            }
            case "M30": {
                return 30;
            }
            case "M53": {
                return 53;
            }
            case "H1": {
                return 60;
            }
            case "H2": {
                return 120;
            }
            case "H4": {
                return 240;
            }
            case "D1": {
                return 1440;
            }
            case "Weekly": {
                return 10080;
            }
            case "Monthly": {
                return 43200;
            }
            case "Intraday": {
                return -10;
            }
        }
        return -2;
    }

    public static String M(int n) {
        return "M" + Integer.toString(n);
    }

    public static long getMillis(String string) throws TradingException {
        if (string.equals(TF_TICK) || string.equals(TF_INTRADAY)) {
            return 0L;
        }
        if (string.equals(TF_WEEKLY)) {
            return 604800000L;
        }
        if (string.equals(TF_MONTHLY)) {
            return 2419200000L;
        }
        String string2 = string.substring(0, 1);
        int n = 0;
        try {
            n = Integer.parseInt(string.substring(1));
        }
        catch (Exception exception) {
            throw new TradingException("Invalid timeframe format. Cannot parse time units count.");
        }
        switch (string2) {
            case "S": {
                return n * 1000;
            }
            case "M": {
                return (long)n * 60000L;
            }
            case "H": {
                return (long)n * 3600000L;
            }
            case "D": {
                return (long)n * 86400000L;
            }
        }
        throw new TradingException("Invalid timeframe format. Prefix '" + string2 + "' not recognized.");
    }

    public static boolean isTimeFrameLessThen(String string, String string2) throws TradingException {
        long l;
        long l2 = TimeframeManager.getMillis(string);
        return l2 < (l = TimeframeManager.getMillis(string2));
    }

    public static long getTFHash(String string) throws TradingException {
        if (string.equals(TF_TICK)) {
            return 0L;
        }
        if (string.equals(TF_INTRADAY)) {
            return -10L;
        }
        if (string.equals(TF_WEEKLY)) {
            return 604800700L;
        }
        if (string.equals(TF_MONTHLY)) {
            return 2419200800L;
        }
        String string2 = string.substring(0, 1);
        int n = 0;
        try {
            n = Integer.parseInt(string.substring(1));
        }
        catch (Exception exception) {
            throw new TradingException("Invalid timeframe format. Cannot parse time units count.");
        }
        switch (string2) {
            case "S": {
                return n * 1000 + 300;
            }
            case "M": {
                return (long)n * 60000L + 400L;
            }
            case "H": {
                return (long)n * 3600000L + 500L;
            }
            case "D": {
                return (long)n * 86400000L + 600L;
            }
        }
        throw new TradingException("Invalid timeframe format. Prefix '" + string2 + "' not recognized.");
    }

    public static String getTFName(long l) {
        if (l < 0L) {
            return TF_INTRADAY;
        }
        if (l == 0L) {
            return TF_TICK;
        }
        String string = "";
        long l2 = 1L;
        if (l < 60000L) {
            string = "S";
            l2 = 1000L;
        } else if (l < 3600000L) {
            string = "M";
            l2 = 60000L;
        } else if (l < 86400000L) {
            if (l % 3600000L != 0L && l % 60000L == 0L) {
                string = "M";
                l2 = 60000L;
            } else {
                string = "H";
                l2 = 3600000L;
            }
        } else if (l < 604800000L) {
            string = "D";
            l2 = 86400000L;
        } else {
            if (l < 2419200000L) {
                return TF_WEEKLY;
            }
            return TF_MONTHLY;
        }
        return string + l / l2;
    }

    public static boolean TFExists(String string) {
        return TimeframeManager.getInstance().defaultTimeframes.contains(string) || TimeframeManager.getInstance().customTimeframes.contains(string);
    }

    private ArrayList<String> _getTimeframes() {
        ArrayList<String> arrayList = new ArrayList<String>(this.defaultTimeframes);
        arrayList.addAll(this.customTimeframes);
        arrayList.sort(new TimeframesComparator());
        return arrayList;
    }

    private void _addTimeframe(String string) throws Exception {
        if (this.customTimeframes.contains(string) || this.defaultTimeframes.contains(string)) {
            throw new Exception("Timeframe '" + string + "' already exists.");
        }
        if (!this.isValid(string)) {
            throw new Exception("Timeframe '" + string + "' has invalid format.");
        }
        this.customTimeframes.add(string);
        SQUtils.arrayListToFile(this.customTimeframes, (String)filePath, (String)delimiter);
    }
}

