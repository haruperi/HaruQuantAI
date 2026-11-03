/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataSeries
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.data.io.TimeframeRecognizer
 *  com.strategyquant.datalib.dataseries.MedianDataSeries
 *  com.strategyquant.datalib.dataseries.TimeDataSeries
 *  com.strategyquant.datalib.dataseries.TypicalDataSeries
 *  com.strategyquant.datalib.dataseries.WeightedDataSeries
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.constants.SQPaths
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.indicatorTester;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.io.TimeframeRecognizer;
import com.strategyquant.datalib.dataseries.MedianDataSeries;
import com.strategyquant.datalib.dataseries.TimeDataSeries;
import com.strategyquant.datalib.dataseries.TypicalDataSeries;
import com.strategyquant.datalib.dataseries.WeightedDataSeries;
import com.strategyquant.indicatorTester.IndicatorTestException;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.indicator.IndicatorsObj;
import com.strategyquant.tradinglib.simulator.Engines;
import java.io.File;
import java.lang.reflect.Method;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.concurrent.locks.ReentrantLock;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class IndicatorTester {
    public static final Logger Log = LoggerFactory.getLogger((String)"IndicatorTester");
    private SimpleDateFormat df = new SimpleDateFormat("yyyy.MM.dd HH:mm:ss");
    private IndicatorsObj indicators;
    public static final int SRC_CHART = 0;
    public static final int SRC_OPEN = 1;
    public static final int SRC_HIGH = 2;
    public static final int SRC_LOW = 3;
    public static final int SRC_CLOSE = 4;
    public static final int SRC_VOLUME = 5;
    public static final int SRC_TYPICAL = 6;
    public static final int SRC_MEDIAN = 7;
    public static final int SRC_WEIGHTED = 8;
    private int startCompareIndex = 400;
    private int maxInvalidLines = 50;
    private String timeframe = "H1";
    private int digits = 5;
    private double tickSize = 1.0E-4;
    private double tickStep = 1.0E-5;
    public String engine = "MetaTrader5 (hedged)";
    private ReentrantLock lock = new ReentrantLock();
    private String errorMsg;
    private ArrayList<String> dataErrors = new ArrayList();
    private boolean showGrid = false;
    private TimeframeRecognizer tfRecognizer = new TimeframeRecognizer();
    private String indicatorTestsPath;

    public void init(String string) throws Exception {
        this.init(string, SQPaths.indicatorTestsPath, this.digits, this.tickSize, this.tickStep);
    }

    public void init(String string, int n, double d, double d2) throws Exception {
        this.init(string, SQPaths.indicatorTestsPath, n, d, d2);
    }

    public void init(String string, String string2, int n, double d, double d2) throws Exception {
        try {
            this.engine = string;
            int n2 = Engines.getEngine(string);
            this.indicators = StrategyBase.createIndicatorsObj(n2);
            this.indicators.Engine = n2;
            this.indicatorTestsPath = string2;
            this.digits = n;
            this.tickSize = d;
            this.tickStep = d2;
        }
        catch (Exception exception) {
            throw new Exception("Initialization of IndicatorTester failed. ", exception);
        }
    }

    public boolean checkFileExists(String string) {
        return new File(this.getFilePath(string)).exists();
    }

    public void runTest(String string, int n, String string2, String string3, Object[] objectArray, int n2, int n3) throws IndicatorTestException {
        if (this.indicators == null) {
            throw new IndicatorTestException(2, new Exception("First init(engine) must be called."));
        }
        this.lock.lock();
        Log.info("--------------------------------------------------------------------------------------------------------------------");
        Log.info("Testing indicator '" + string2 + "' using source file '" + string + "', engine=" + this.engine);
        DataSeries dataSeries = new DataSeries();
        DataSeries dataSeries2 = new DataSeries();
        ChartData chartData = null;
        try {
            String string4 = this.getFilePath(string);
            File file = new File(string4);
            try {
                chartData = this.loadSourceData(string4, dataSeries2);
            }
            catch (Exception exception) {
                throw new IndicatorTestException(1, exception);
            }
            if (dataSeries2.size() == 0) {
                throw new IndicatorTestException(5, new Exception(file.getAbsolutePath()));
            }
            try {
                objectArray = objectArray == null ? new Object[]{} : objectArray;
                Object[] objectArray2 = new Object[objectArray.length + 1];
                objectArray2[0] = this.getSourceData(chartData, n);
                System.arraycopy(objectArray, 0, objectArray2, 1, objectArray.length);
                Object object = this.callMethod(this.indicators, string2, objectArray2);
                dataSeries = (DataSeries)object.getClass().getField(string3).get(object);
                dataSeries.setShift(n3);
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Cannot instantiate indicator '%s'!", (Object[])new Object[]{string2}), exception);
            }
            int n4 = chartData.Time.size() - this.startCompareIndex - 1;
            int n5 = 0;
            dataSeries.get(0);
            for (int i = n4; i >= 0; --i) {
                double d = dataSeries.get(i);
                if (this.checkPrecision(d, dataSeries2.get(i), n2)) continue;
                String string5 = this.df.format(new Date(chartData.Time(i))) + "," + d + "," + dataSeries2.get(i);
                this.showGrid = true;
                this.dataErrors.add(string5);
                Log.debug(file.getName() + " - " + string5);
                if (++n5 <= 150) continue;
                this.errorMsg = "more than 150 differences";
                throw new IndicatorTestException(3, new Exception(this.errorMsg));
            }
            if (n5 > 0) {
                this.errorMsg = n5 + " differences";
            }
        }
        catch (IndicatorTestException indicatorTestException) {
            throw indicatorTestException;
        }
        catch (Exception exception) {
            this.errorMsg = exception.getMessage();
            this.dataErrors.add(SQUtils.stackTraceToString((Throwable)exception));
            throw new IndicatorTestException(4, exception);
        }
        finally {
            dataSeries.destroy();
            dataSeries2.destroy();
            if (chartData != null) {
                chartData.destroy();
            }
            this.lock.unlock();
        }
    }

    public void runTest(String string, int n, int n2, int n3, int n4, String string2, String string3, String string4, String string5, String string6, String string7, String string8, String string9, Object[] objectArray, Object[] objectArray2, Object[] objectArray3, Object[] objectArray4, String string10, int n5, int n6, int n7, int n8, boolean bl) throws IndicatorTestException {
        if (this.indicators == null) {
            throw new IndicatorTestException(2, new Exception("First init(engine) must be called."));
        }
        this.lock.lock();
        Log.info("--------------------------------------------------------------------------------------------------------------------");
        Log.info("Testing indicator '" + string2 + "' using source file '" + string + "', engine=" + this.engine);
        DataSeries dataSeries = new DataSeries();
        DataSeries dataSeries2 = new DataSeries();
        DataSeries dataSeries3 = new DataSeries();
        DataSeries dataSeries4 = new DataSeries();
        DataSeries dataSeries5 = new DataSeries();
        ChartData chartData = null;
        try {
            int n9;
            String string11 = this.getFilePath(string);
            File file = new File(string11);
            try {
                chartData = this.loadSourceData(string11, dataSeries5, bl);
            }
            catch (Exception exception) {
                throw new IndicatorTestException(1, exception);
            }
            if (dataSeries5.size() == 0) {
                throw new IndicatorTestException(5, new Exception(file.getAbsolutePath()));
            }
            int n10 = Engines.getEngine(this.engine);
            IndicatorsObj indicatorsObj = StrategyBase.createIndicatorsObj(n10);
            indicatorsObj.Engine = n10;
            try {
                Object object;
                Object[] objectArray5;
                if (string2.length() >= 6 && string2.equals("Volume")) {
                    dataSeries = chartData.Volume;
                } else if (string2.equals("Open") || string2.startsWith("Open") && string2.length() == 5) {
                    dataSeries = chartData.Open;
                } else if (string2.equals("High") || string2.startsWith("High") && string2.length() == 5) {
                    dataSeries = chartData.High;
                } else if (string2.equals("Low") || string2.startsWith("Low") && string2.length() == 4) {
                    dataSeries = chartData.Low;
                } else if (string2.equals("Close") || string2.startsWith("Close") && string2.length() == 6) {
                    dataSeries = chartData.Close;
                } else {
                    objectArray = objectArray == null ? new Object[]{} : objectArray;
                    objectArray5 = new Object[objectArray.length + 1];
                    objectArray5[0] = this.getSourceData(chartData, n);
                    System.arraycopy(objectArray, 0, objectArray5, 1, objectArray.length);
                    object = this.callMethod(indicatorsObj, string2, objectArray5);
                    dataSeries = (DataSeries)object.getClass().getField(string6).get(object);
                }
                if (!string3.equals("") && !string7.equals("")) {
                    if (string3.length() >= 6 && string3.equals("Volume")) {
                        dataSeries2 = chartData.Volume;
                    } else if (string3.equals("Open") || string3.startsWith("Open") && string3.length() == 5) {
                        dataSeries2 = chartData.Open;
                    } else if (string3.equals("High") || string3.startsWith("High") && string3.length() == 5) {
                        dataSeries2 = chartData.High;
                    } else if (string3.equals("Low") || string3.startsWith("Low") && string3.length() == 4) {
                        dataSeries2 = chartData.Low;
                    } else if (string3.equals("Close") || string3.startsWith("Close") && string3.length() == 6) {
                        dataSeries2 = chartData.Close;
                    } else {
                        objectArray2 = objectArray2 == null ? new Object[]{} : objectArray2;
                        objectArray5 = new Object[objectArray2.length + 1];
                        objectArray5[0] = this.getSourceData(chartData, n2);
                        System.arraycopy(objectArray2, 0, objectArray5, 1, objectArray2.length);
                        object = this.callMethod(indicatorsObj, string3, objectArray5);
                        dataSeries2 = (DataSeries)object.getClass().getField(string7).get(object);
                    }
                } else {
                    dataSeries2 = dataSeries;
                }
                if (!string4.equals("") && !string8.equals("")) {
                    if (string4.length() >= 6 && string4.equals("Volume")) {
                        dataSeries3 = chartData.Volume;
                    } else if (string4.equals("Open") || string4.startsWith("Open") && string4.length() == 5) {
                        dataSeries3 = chartData.Open;
                    } else if (string4.equals("High") || string4.startsWith("High") && string4.length() == 5) {
                        dataSeries3 = chartData.High;
                    } else if (string4.equals("Low") || string4.startsWith("Low") && string4.length() == 4) {
                        dataSeries3 = chartData.Low;
                    } else if (string4.equals("Close") || string4.startsWith("Close") && string4.length() == 6) {
                        dataSeries3 = chartData.Close;
                    } else {
                        objectArray3 = objectArray3 == null ? new Object[]{} : objectArray3;
                        objectArray5 = new Object[objectArray3.length + 1];
                        objectArray5[0] = this.getSourceData(chartData, n3);
                        System.arraycopy(objectArray3, 0, objectArray5, 1, objectArray3.length);
                        object = this.callMethod(indicatorsObj, string4, objectArray5);
                        dataSeries3 = (DataSeries)object.getClass().getField(string8).get(object);
                    }
                } else {
                    dataSeries3 = dataSeries;
                }
                if (!string5.equals("") && !string9.equals("")) {
                    if (string5.length() >= 6 && string5.equals("Volume")) {
                        dataSeries4 = chartData.Volume;
                    } else if (string5.equals("Open") || string5.startsWith("Open") && string5.length() == 5) {
                        dataSeries4 = chartData.Open;
                    } else if (string5.equals("High") || string5.startsWith("High") && string5.length() == 5) {
                        dataSeries4 = chartData.High;
                    } else if (string5.equals("Low") || string5.startsWith("Low") && string5.length() == 4) {
                        dataSeries4 = chartData.Low;
                    } else if (string5.equals("Close") || string5.startsWith("Close") && string5.length() == 6) {
                        dataSeries4 = chartData.Close;
                    } else {
                        objectArray4 = objectArray4 == null ? new Object[]{} : objectArray4;
                        objectArray5 = new Object[objectArray4.length + 1];
                        objectArray5[0] = this.getSourceData(chartData, n4);
                        System.arraycopy(objectArray4, 0, objectArray5, 1, objectArray4.length);
                        object = this.callMethod(indicatorsObj, string5, objectArray5);
                        dataSeries4 = (DataSeries)object.getClass().getField(string9).get(object);
                    }
                } else {
                    dataSeries4 = dataSeries;
                }
                dataSeries.setShift(n6);
                dataSeries2.setShift(n6);
                dataSeries3.setShift(n6);
                dataSeries4.setShift(n6);
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Cannot instantiate indicator '%s'!", (Object[])new Object[]{string2}), exception);
            }
            int n11 = chartData.Time.size() - 1 - 1;
            int n12 = 0;
            int n13 = 0;
            int n14 = 0;
            int n15 = 0;
            int n16 = 0;
            int n17 = 0;
            int n18 = 0;
            boolean bl2 = false;
            boolean bl3 = false;
            boolean bl4 = false;
            boolean bl5 = false;
            boolean bl6 = false;
            boolean bl7 = false;
            boolean bl8 = false;
            dataSeries.get(0);
            if (!string7.equals("")) {
                dataSeries2.get(0);
            }
            for (n9 = n11; n9 >= 0; --n9) {
                double d = dataSeries.get(n9);
                if (string2.equals("OpenD")) {
                    d = chartData.OpenD(n9);
                }
                if (string2.equals("HighD")) {
                    d = chartData.HighD(n9);
                }
                if (string2.equals("LowD")) {
                    d = chartData.LowD(n9);
                }
                if (string2.equals("CloseD")) {
                    d = chartData.CloseD(n9);
                }
                if (string2.equals("OpenW")) {
                    d = chartData.OpenW(n9);
                }
                if (string2.equals("HighW")) {
                    d = chartData.HighW(n9);
                }
                if (string2.equals("LowW")) {
                    d = chartData.LowW(n9);
                }
                if (string2.equals("CloseW")) {
                    d = chartData.CloseW(n9);
                }
                if (string2.equals("OpenM")) {
                    d = chartData.OpenM(n9);
                }
                if (string2.equals("HighM")) {
                    d = chartData.HighM(n9);
                }
                if (string2.equals("LowM")) {
                    d = chartData.LowM(n9);
                }
                if (string2.equals("CloseM")) {
                    d = chartData.CloseM(n9);
                }
                if (!string10.equals("")) {
                    if (this.isConditionMet(chartData, string2, string10, dataSeries, dataSeries2, dataSeries3, dataSeries4, n9)) {
                        d = 1.0;
                        continue;
                    }
                    d = 0.0;
                    continue;
                }
                if (!bl2 && this.checkPrecision(d, dataSeries5.get(n9), 1)) {
                    bl2 = true;
                    n12 = n11 - n9;
                }
                if (!this.checkPrecision(d, dataSeries5.get(n9), 1)) {
                    bl2 = false;
                }
                if (!bl3 && this.checkPrecision(d, dataSeries5.get(n9), 2)) {
                    bl3 = true;
                    n13 = n11 - n9;
                }
                if (!this.checkPrecision(d, dataSeries5.get(n9), 2)) {
                    bl3 = false;
                }
                if (!bl4 && this.checkPrecision(d, dataSeries5.get(n9), 3)) {
                    bl4 = true;
                    n14 = n11 - n9;
                }
                if (!this.checkPrecision(d, dataSeries5.get(n9), 3)) {
                    bl4 = false;
                }
                if (!bl5 && this.checkPrecision(d, dataSeries5.get(n9), 4)) {
                    bl5 = true;
                    n15 = n11 - n9;
                }
                if (!this.checkPrecision(d, dataSeries5.get(n9), 4)) {
                    bl5 = false;
                }
                if (!bl6 && this.checkPrecision(d, dataSeries5.get(n9), 5)) {
                    bl6 = true;
                    n16 = n11 - n9;
                }
                if (!this.checkPrecision(d, dataSeries5.get(n9), 5)) {
                    bl6 = false;
                }
                if (!bl7 && this.checkPrecision(d, dataSeries5.get(n9), 6)) {
                    bl7 = true;
                    n17 = n11 - n9;
                }
                if (!this.checkPrecision(d, dataSeries5.get(n9), 6)) {
                    bl7 = false;
                }
                if (!bl8 && this.checkPrecision(d, dataSeries5.get(n9), 7)) {
                    bl8 = true;
                    n18 = n11 - n9;
                }
                if (this.checkPrecision(d, dataSeries5.get(n9), 7)) continue;
                bl8 = false;
            }
            if (string10.equals("")) {
                Log.info(this.engine + "   " + string + "  :  " + n12 + " reserved bars " + this.timeframe + " are necessary for a precision 1 decimals ");
                Log.info(this.engine + "   " + string + "  :  " + n13 + " reserved bars " + this.timeframe + " are necessary for a precision 2 decimals ");
                Log.info(this.engine + "   " + string + "  :  " + n14 + " reserved bars " + this.timeframe + " are necessary for a precision 3 decimals ");
                Log.info(this.engine + "   " + string + "  :  " + n15 + " reserved bars " + this.timeframe + " are necessary for a precision 4 decimals ");
                Log.info(this.engine + "   " + string + "  :  " + n16 + " reserved bars " + this.timeframe + " are necessary for a precision 5 decimals ");
                Log.info(this.engine + "   " + string + "  :  " + n17 + " reserved bars " + this.timeframe + " are necessary for a precision 6 decimals ");
                Log.info(this.engine + "   " + string + "  :  " + n18 + " reserved bars " + this.timeframe + " are necessary for a precision 7 decimals ");
            }
            n11 = chartData.Time.size() - n7 - 1;
            n9 = 0;
            dataSeries.get(0);
            if (!string7.equals("")) {
                dataSeries2.get(0);
            }
            for (int i = n11; i >= 0; --i) {
                double d = dataSeries.get(i);
                if (string2.equals("OpenD")) {
                    d = chartData.OpenD(i);
                }
                if (string2.equals("HighD")) {
                    d = chartData.HighD(i);
                }
                if (string2.equals("LowD")) {
                    d = chartData.LowD(i);
                }
                if (string2.equals("CloseD")) {
                    d = chartData.CloseD(i);
                }
                if (string2.equals("OpenW")) {
                    d = chartData.OpenW(i);
                }
                if (string2.equals("HighW")) {
                    d = chartData.HighW(i);
                }
                if (string2.equals("LowW")) {
                    d = chartData.LowW(i);
                }
                if (string2.equals("CloseW")) {
                    d = chartData.CloseW(i);
                }
                if (string2.equals("OpenM")) {
                    d = chartData.OpenM(i);
                }
                if (string2.equals("HighM")) {
                    d = chartData.HighM(i);
                }
                if (string2.equals("LowM")) {
                    d = chartData.LowM(i);
                }
                if (string2.equals("CloseM")) {
                    d = chartData.CloseM(i);
                }
                if (!string10.equals("")) {
                    d = this.isConditionMet(chartData, string2, string10, dataSeries, dataSeries2, dataSeries3, dataSeries4, i) ? 1.0 : 0.0;
                }
                if (!this.checkPrecision(d, dataSeries5.get(i), n5)) {
                    String string12 = this.df.format(new Date(chartData.Time(i))) + "," + d + "," + dataSeries5.get(i);
                    this.showGrid = true;
                    this.dataErrors.add(string12);
                    Log.error(file.getName() + " - " + string12);
                    ++n9;
                }
                if (n9 < n8) continue;
                this.errorMsg = this.engine + "   " + string + "  :  Failed with " + n7 + " " + this.timeframe + " reserved bars and " + n5 + " decimals   with more than  " + n9 + " differences";
                throw new IndicatorTestException(3, new Exception(this.errorMsg));
            }
            if (n9 > 0) {
                this.errorMsg = n9 + " differences";
            }
        }
        catch (IndicatorTestException indicatorTestException) {
            throw indicatorTestException;
        }
        catch (Exception exception) {
            this.errorMsg = exception.getMessage();
            this.dataErrors.add(SQUtils.stackTraceToString((Throwable)exception));
            throw new IndicatorTestException(4, exception);
        }
        finally {
            dataSeries.destroy();
            dataSeries2.destroy();
            dataSeries3.destroy();
            dataSeries4.destroy();
            dataSeries5.destroy();
            if (chartData != null) {
                chartData.destroy();
            }
            this.lock.unlock();
        }
    }

    public boolean isConditionMet(ChartData chartData, String string, String string2, DataSeries dataSeries, DataSeries dataSeries2, DataSeries dataSeries3, DataSeries dataSeries4, int n) throws Exception {
        if (n + 1 >= dataSeries.size() || n + 1 >= dataSeries2.size() || n + 1 >= dataSeries3.size() || n + 1 >= dataSeries4.size()) {
            return false;
        }
        double d = dataSeries.get(n);
        double d2 = dataSeries.get(n + 1);
        double d3 = dataSeries.get(n + 2);
        double d4 = dataSeries2.get(n);
        double d5 = dataSeries2.get(n + 1);
        double d6 = dataSeries2.get(n + 2);
        double d7 = dataSeries3.get(n);
        double d8 = dataSeries3.get(n + 1);
        double d9 = dataSeries3.get(n + 2);
        Object var27_18 = null;
        switch (string2) {
            case "ADXRising": {
                return dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "ADXFalling": {
                return dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "ADXSup50": {
                return dataSeries.getRounded(n) > 50.0;
            }
            case "ADXInf50": {
                return dataSeries.getRounded(n) < 50.0;
            }
            case "ADXCrossAbove50": {
                return dataSeries.getRounded(n + 1) < 50.0 && dataSeries.getRounded(n) > 50.0;
            }
            case "ADXCrossbelow50": {
                return dataSeries.getRounded(n + 1) > 50.0 && dataSeries.getRounded(n) < 50.0;
            }
            case "ADXChangeDirectionUpward": {
                return dataSeries.getRounded(n + 2) > dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "ADXChangeDirectionDownward": {
                return dataSeries.getRounded(n + 2) < dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "AwesomeOscillatorRising": {
                return dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "AwesomeOscillatorFalling": {
                return dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "AwesomeOscillatorSup50": {
                return dataSeries.getRounded(n) > 50.0;
            }
            case "AwesomeOscillatorInf50": {
                return dataSeries.getRounded(n) < 50.0;
            }
            case "AwesomeOscillatorCrossAbove50": {
                return dataSeries.getRounded(n + 1) < 50.0 && dataSeries.getRounded(n) > 50.0;
            }
            case "AwesomeOscillatorCrossbelow50": {
                return dataSeries.getRounded(n + 1) > 50.0 && dataSeries.getRounded(n) < 50.0;
            }
            case "AwesomeOscillatorChangeDirectionUpward": {
                return dataSeries.getRounded(n + 2) > dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "AwesomeOscillatorChangeDirectionDownward": {
                return dataSeries.getRounded(n + 2) < dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "BearsPowerRising": {
                return dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "BearsPowerFalling": {
                return dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "BearsPowerSup50": {
                return dataSeries.getRounded(n) > 50.0;
            }
            case "BearsPowerInf50": {
                return dataSeries.getRounded(n) < 50.0;
            }
            case "BearsPowerCrossAbove50": {
                return dataSeries.getRounded(n + 1) < 50.0 && dataSeries.getRounded(n) > 50.0;
            }
            case "BearsPowerCrossbelow50": {
                return dataSeries.getRounded(n + 1) > 50.0 && dataSeries.getRounded(n) < 50.0;
            }
            case "BearsPowerChangeDirectionUpward": {
                return dataSeries.getRounded(n + 2) > dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "BearsPowerChangeDirectionDownward": {
                return dataSeries.getRounded(n + 2) < dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "BullsPowerRising": {
                return dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "BullsPowerFalling": {
                return dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "BullsPowerSup50": {
                return dataSeries.getRounded(n) > 50.0;
            }
            case "BullsPowerInf50": {
                return dataSeries.getRounded(n) < 50.0;
            }
            case "BullsPowerCrossAbove50": {
                return dataSeries.getRounded(n + 1) < 50.0 && dataSeries.getRounded(n) > 50.0;
            }
            case "BullsPowerCrossbelow50": {
                return dataSeries.getRounded(n + 1) > 50.0 && dataSeries.getRounded(n) < 50.0;
            }
            case "BullsPowerChangeDirectionUpward": {
                return dataSeries.getRounded(n + 2) > dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "BullsPowerChangeDirectionDownward": {
                return dataSeries.getRounded(n + 2) < dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "ATR14_Rising": {
                return dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "ATR14_Falling": {
                return dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "ATR14_Sup50": {
                return dataSeries.getRounded(n) > 50.0;
            }
            case "ATR14_Inf50": {
                return dataSeries.getRounded(n) < 50.0;
            }
            case "ATR14_CrossAbove50": {
                return dataSeries.getRounded(n + 1) < 50.0 && dataSeries.getRounded(n) > 50.0;
            }
            case "ATR14_Crossbelow50": {
                return dataSeries.getRounded(n + 1) > 50.0 && dataSeries.getRounded(n) < 50.0;
            }
            case "ATR14_ChangeDirectionUpward": {
                return dataSeries.getRounded(n + 2) > dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "ATR14_ChangeDirectionDownward": {
                return dataSeries.getRounded(n + 2) < dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "AROON14_AroonDownFallsFromTop": {
                return dataSeries2.getRounded(n + 1) == 100.0 && dataSeries2.getRounded(n) < 100.0 && dataSeries.getRounded(n) < 70.0;
            }
            case "AROON14_AroonDownRisesFromBottom": {
                return dataSeries2.getRounded(n + 1) <= 8.0 && dataSeries2.getRounded(n) > 8.0 && dataSeries.getRounded(n) > 30.0;
            }
            case "AROON14_AroonUpCrossesAboveAroonDown": {
                return dataSeries.getRounded(n + 1) < dataSeries2.getRounded(n + 1) && dataSeries.getRounded(n) > dataSeries2.getRounded(n);
            }
            case "AROON14_AroonUpCrossesBelowAroonDown": {
                return dataSeries.getRounded(n + 1) > dataSeries2.getRounded(n + 1) && dataSeries.getRounded(n) < dataSeries2.getRounded(n);
            }
            case "AROON14_AroonUpFallsFromTop": {
                return dataSeries.getRounded(n + 1) == 100.0 && dataSeries.getRounded(n) < 100.0 && dataSeries2.getRounded(n) < 70.0;
            }
            case "AROON14_AroonUpRisesFromBottom": {
                return dataSeries.getRounded(n + 1) <= 8.0 && dataSeries.getRounded(n) > 8.0 && dataSeries2.getRounded(n) > 30.0;
            }
            case "AVGVOLUME_14_VolumeIsFalling": {
                double d10 = dataSeries.getRounded(n + 1, 4);
                double d11 = dataSeries.getRounded(n, 4);
                return d10 > d11;
            }
            case "AVGVOLUME_14_VolumeIsRising": {
                double d12 = dataSeries.getRounded(n + 1, 4);
                double d13 = dataSeries.getRounded(n, 4);
                return d12 < d13;
            }
            case "VolumeIsFalling": {
                double d14 = dataSeries.getRounded(n + 1);
                double d15 = dataSeries.getRounded(n);
                return d14 > d15;
            }
            case "VolumeIsRising": {
                double d16 = dataSeries.getRounded(n + 1);
                double d17 = dataSeries.getRounded(n);
                return d16 < d17;
            }
            case "BB_CLOSE_20_0.75_LowerBandIsFalling": {
                return dataSeries2.getRounded(n + 1) > dataSeries2.getRounded(n);
            }
            case "BB_CLOSE_20_0.75_LowerBandIsRising": {
                return dataSeries2.getRounded(n + 1) < dataSeries2.getRounded(n);
            }
            case "BB_CLOSE_20_0.75_UpperBandIsFalling": {
                return dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "BB_CLOSE_20_0.75_UpperBandIsRising": {
                return dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "BB_CLOSE_20_0.75_BarClosesAboveLowerBand": {
                return chartData.Close(n) > dataSeries2.getRounded(n);
            }
            case "BB_CLOSE_20_0.75_BarClosesAboveUpperBand": {
                return chartData.Close(n) > dataSeries.getRounded(n);
            }
            case "BB_CLOSE_20_0.75_BarClosesBelowLowerBand": {
                return chartData.Close(n) < dataSeries2.getRounded(n);
            }
            case "BB_CLOSE_20_0.75_BarClosesBelowUpperBand": {
                return chartData.Close(n) < dataSeries.getRounded(n);
            }
            case "BB_CLOSE_20_0.75_BarOpensAboveLowerBand": {
                return chartData.Open(n) > dataSeries2.getRounded(n + 1);
            }
            case "BB_CLOSE_20_0.75_BarOpensAboveUpperBand": {
                return chartData.Open(n) > dataSeries.getRounded(n + 1);
            }
            case "BB_CLOSE_20_0.75_BarOpensBelowLowerBand": {
                return chartData.Open(n) < dataSeries2.getRounded(n + 1);
            }
            case "BB_CLOSE_20_0.75_BarOpensBelowUpperBand": {
                return chartData.Open(n) < dataSeries.getRounded(n + 1);
            }
            case "BB_CLOSE_20_0.75_BarOpensAboveLowerBandAfterOpenedBelow": {
                return chartData.Open(n + 1) < dataSeries2.getRounded(n + 1) && chartData.Open(n) > dataSeries2.getRounded(n + 1);
            }
            case "BB_CLOSE_20_0.75_BarOpensAboveUpperBandAfterOpenedBelow": {
                return chartData.Open(n + 1) < dataSeries.getRounded(n + 1) && chartData.Open(n) > dataSeries.getRounded(n + 1);
            }
            case "BB_CLOSE_20_0.75_BarOpensBelowLowerBandAfterOpenedAbove": {
                return chartData.Open(n + 1) > dataSeries2.getRounded(n + 1) && chartData.Open(n) < dataSeries2.getRounded(n + 1);
            }
            case "BB_CLOSE_20_0.75_BarOpensBelowUpperBandAfterOpenedAbove": {
                return chartData.Open(n + 1) > dataSeries.getRounded(n + 1) && chartData.Open(n) < dataSeries.getRounded(n + 1);
            }
            case "CCI_Rising": {
                return dataSeries.getRounded(n + 1, 4) < dataSeries.getRounded(n, 4);
            }
            case "CCI_Falling": {
                return dataSeries.getRounded(n + 1, 4) > dataSeries.getRounded(n, 4);
            }
            case "CCI_Sup50": {
                return dataSeries.getRounded(n, 4) > 50.0;
            }
            case "CCI_Inf50": {
                return dataSeries.getRounded(n, 4) < 50.0;
            }
            case "CCI_CrossAbove50": {
                return dataSeries.getRounded(n + 1, 4) < 50.0 && dataSeries.getRounded(n, 4) > 50.0;
            }
            case "CCI_Crossbelow50": {
                return dataSeries.getRounded(n + 1, 4) > 50.0 && dataSeries.getRounded(n, 4) < 50.0;
            }
            case "CCI_30_CrossAbove0": {
                return dataSeries.getRounded(n + 1, 4) < 0.0 && dataSeries.getRounded(n, 4) > 0.0;
            }
            case "CCI_30_Crossbelow0": {
                return dataSeries.getRounded(n + 1, 4) > 0.0 && dataSeries.getRounded(n, 4) < 0.0;
            }
            case "CCI_ChangeDirectionUpward": {
                return dataSeries.getRounded(n + 2, 4) > dataSeries.getRounded(n + 1, 4) && dataSeries.getRounded(n + 1, 4) < dataSeries.getRounded(n, 4);
            }
            case "CCI_ChangeDirectionDownward": {
                return dataSeries.getRounded(n + 2, 4) < dataSeries.getRounded(n + 1, 4) && dataSeries.getRounded(n + 1, 4) > dataSeries.getRounded(n, 4);
            }
            case "WoodiesCCIZeroLineBreakDown": {
                return dataSeries.getRounded(n + 1) > 0.0 && dataSeries.getRounded(n) < 0.0;
            }
            case "WoodiesCCIZeroLineBreakUP": {
                return dataSeries.getRounded(n + 1) < 0.0 && dataSeries.getRounded(n) > 0.0;
            }
            case "WoodiesFamirDown": {
                double d18 = dataSeries.getRounded(n + 1);
                double d19 = dataSeries.getRounded(n + 2);
                double d20 = dataSeries.getRounded(n + 3);
                double d21 = dataSeries.getRounded(n + 4);
                double d22 = dataSeries.getRounded(n + 5);
                double d23 = dataSeries.getRounded(n + 6);
                double d24 = dataSeries.getRounded(n);
                double d25 = 5.0;
                boolean bl = d18 > d19 && d20 > d19 && d24 < d18;
                boolean bl2 = d18 - d19 > d25 && d20 - d19 > d25;
                return d24 < 50.0 && d18 > 0.0 && d19 > 0.0 && d20 > 0.0 && d21 > 0.0 && d22 > 0.0 && d23 > 0.0 && bl && bl2;
            }
            case "WoodiesFamirUP": {
                double d26 = dataSeries.getRounded(n + 1);
                double d27 = dataSeries.getRounded(n + 2);
                double d28 = dataSeries.getRounded(n + 3);
                double d29 = dataSeries.getRounded(n + 4);
                double d30 = dataSeries.getRounded(n + 5);
                double d31 = dataSeries.getRounded(n + 6);
                double d32 = dataSeries.getRounded(n);
                double d33 = 5.0;
                boolean bl = d26 < d27 && d28 < d27 && d32 > d26;
                boolean bl3 = d27 - d26 > d33 && d27 - d28 > d33;
                return d32 > -50.0 && d26 < 0.0 && d27 < 0.0 && d28 < 0.0 && d29 < 0.0 && d30 < 0.0 && d31 < 0.0 && bl && bl3;
            }
            case "WoodiesTrendDown": {
                double d34 = dataSeries.getRounded(n + 1);
                double d35 = dataSeries.getRounded(n + 2);
                double d36 = dataSeries.getRounded(n + 3);
                double d37 = dataSeries.getRounded(n + 4);
                double d38 = dataSeries.getRounded(n + 5);
                double d39 = dataSeries.getRounded(n);
                return d34 < 0.0 && d35 < 0.0 && d36 < 0.0 && d37 < 0.0 && d38 < 0.0 && d39 < 0.0;
            }
            case "WoodiesTrendUP": {
                double d40 = dataSeries.getRounded(n + 1);
                double d41 = dataSeries.getRounded(n + 2);
                double d42 = dataSeries.getRounded(n + 3);
                double d43 = dataSeries.getRounded(n + 4);
                double d44 = dataSeries.getRounded(n + 5);
                double d45 = dataSeries.getRounded(n);
                return d40 > 0.0 && d41 > 0.0 && d42 > 0.0 && d43 > 0.0 && d44 > 0.0 && d45 > 0.0;
            }
            case "WoodiesVegasTradeDown": {
                double d46 = dataSeries.getRounded(n + 1);
                double d47 = dataSeries.getRounded(n + 2);
                double d48 = dataSeries.getRounded(n + 3);
                double d49 = dataSeries.getRounded(n + 4);
                double d50 = dataSeries.getRounded(n + 5);
                double d51 = dataSeries.getRounded(n + 6);
                double d52 = dataSeries.getRounded(n);
                double d53 = 5.0;
                boolean bl = d49 - d48 > d53 && d46 - d47 > d53;
                boolean bl4 = d46 > 0.0 && d47 > 0.0 && d48 > 0.0 && d49 > 0.0 && d50 > 0.0 && d51 > 0.0;
                boolean bl5 = d46 > d47 && d46 > d48 && d49 > d47 && d49 > d48;
                boolean bl6 = d46 > 200.0 || d47 > 200.0 || d48 > 200.0 || d49 > 200.0 || d50 > 200.0;
                return bl6 && bl5 && bl && bl4 && d52 < (d48 + d47) / 2.0;
            }
            case "WoodiesVegasTradeUP": {
                double d54 = dataSeries.getRounded(n + 1);
                double d55 = dataSeries.getRounded(n + 2);
                double d56 = dataSeries.getRounded(n + 3);
                double d57 = dataSeries.getRounded(n + 4);
                double d58 = dataSeries.getRounded(n + 5);
                double d59 = dataSeries.getRounded(n + 6);
                double d60 = dataSeries.getRounded(n);
                double d61 = 5.0;
                boolean bl = d55 - d54 > d61 && d56 - d57 > d61;
                boolean bl7 = d54 < 0.0 && d55 < 0.0 && d56 < 0.0 && d57 < 0.0 && d58 < 0.0 && d59 < 0.0;
                boolean bl8 = d54 < d55 && d54 < d56 && d57 < d55 && d57 < d56;
                boolean bl9 = d54 < -200.0 || d55 < -200.0 || d56 < -200.0 || d57 < -200.0 || d58 < -200.0;
                return bl9 && bl8 && bl && bl7 && d60 > (d56 + d55) / 2.0;
            }
            case "WoodiesZLRDown": {
                double d62 = dataSeries.getRounded(n + 1);
                double d63 = dataSeries.getRounded(n + 2);
                double d64 = dataSeries.getRounded(n + 3);
                double d65 = dataSeries.getRounded(n + 4);
                double d66 = dataSeries.getRounded(n + 5);
                double d67 = dataSeries.getRounded(n);
                double d68 = 5.0;
                boolean bl = d67 < d62 && d63 < d62;
                boolean bl10 = d62 - d67 > d68 && d62 - d63 > d68;
                boolean bl11 = d67 < 100.0 && d62 < 100.0 && d63 < 100.0;
                boolean bl12 = d67 > -100.0 && d62 > -100.0 && d63 > -100.0;
                return d62 < 0.0 && d63 < 0.0 && d64 < 0.0 && d65 < 0.0 && d66 < 0.0 && d67 < 0.0 && bl && bl10 && bl11 && bl12;
            }
            case "WoodiesZLRUP": {
                double d69 = dataSeries.getRounded(n + 1);
                double d70 = dataSeries.getRounded(n + 2);
                double d71 = dataSeries.getRounded(n + 3);
                double d72 = dataSeries.getRounded(n + 4);
                double d73 = dataSeries.getRounded(n + 5);
                double d74 = dataSeries.getRounded(n);
                double d75 = 5.0;
                boolean bl = d74 > d69 && d70 > d69;
                boolean bl13 = d74 - d69 > d75 && d70 - d69 > d75;
                boolean bl14 = d74 < 100.0 && d69 < 100.0 && d70 < 100.0;
                boolean bl15 = d74 > -100.0 && d69 > -100.0 && d70 > -100.0;
                return d69 > 0.0 && d70 > 0.0 && d71 > 0.0 && d72 > 0.0 && d73 > 0.0 && d74 > 0.0 && bl && bl13 && bl14 && bl15;
            }
            case "DeMarker_Rising": {
                return dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "DeMarker_Falling": {
                return dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "DeMarker_Sup05": {
                return dataSeries.getRounded(n) > 0.5;
            }
            case "DeMarker_Inf05": {
                return dataSeries.getRounded(n) < 0.5;
            }
            case "DeMarker_CrossAbove05": {
                return dataSeries.getRounded(n + 1) < 0.5 && dataSeries.getRounded(n) > 0.5;
            }
            case "DeMarker_Crossbelow05": {
                return dataSeries.getRounded(n + 1) > 0.5 && dataSeries.getRounded(n) < 0.5;
            }
            case "DeMarker_ChangeDirectionUpward": {
                return dataSeries.getRounded(n + 2) > dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "DeMarker_ChangeDirectionDownward": {
                return dataSeries.getRounded(n + 2) < dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "DICrossDown": {
                double d76 = dataSeries.getRounded(n + 1);
                double d77 = dataSeries2.getRounded(n + 1);
                double d78 = dataSeries.getRounded(n);
                double d79 = dataSeries2.getRounded(n);
                return d76 > d77 && d78 < d79;
            }
            case "DICrossUp": {
                double d80 = dataSeries.getRounded(n + 1);
                double d81 = dataSeries2.getRounded(n + 1);
                double d82 = dataSeries.getRounded(n);
                double d83 = dataSeries2.getRounded(n);
                return d80 < d81 && d82 > d83;
            }
            case "DIM_ChangeDirectionDownward": {
                return dataSeries.getRounded(n + 2) < dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "DIM_ChangeDirectionUpward": {
                return dataSeries.getRounded(n + 2) > dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "DIM_Falling": {
                return dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "DIM_Rising": {
                return dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "DIP_ChangeDirectionDownward": {
                return dataSeries.getRounded(n + 2) < dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "DIP_ChangeDirectionUpward": {
                return dataSeries.getRounded(n + 2) > dataSeries.getRounded(n + 1) && dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "DIP_Falling": {
                return dataSeries.getRounded(n + 1) > dataSeries.getRounded(n);
            }
            case "DIPlusHigher": {
                double d84 = dataSeries.getRounded(n);
                double d85 = dataSeries2.getRounded(n);
                return d84 > d85;
            }
            case "DIPlusLower": {
                double d86 = dataSeries.getRounded(n);
                double d87 = dataSeries2.getRounded(n);
                return d86 < d87;
            }
            case "DIP_Rising": {
                return dataSeries.getRounded(n + 1) < dataSeries.getRounded(n);
            }
            case "BearishEngulfing": {
                double d88 = chartData.Open(n);
                double d89 = chartData.Open(n + 1);
                double d90 = chartData.Close(n);
                double d91 = chartData.Close(n + 1);
                return d91 > d89 && d88 > d90 && d88 >= d91 && d89 >= d90 && d88 - d90 > d91 - d89;
            }
            case "BullishEngulfing": {
                double d92 = chartData.Open(n);
                double d93 = chartData.Open(n + 1);
                double d94 = chartData.Close(n);
                double d95 = chartData.Close(n + 1);
                return d93 > d95 && d94 > d92 && d94 >= d93 && d95 >= d92 && d94 - d92 > d93 - d95;
            }
            case "DarkCloud": {
                double d96 = chartData.Open(n);
                double d97 = chartData.Open(n + 1);
                double d98 = chartData.Close(n);
                double d99 = chartData.Close(n + 1);
                double d100 = chartData.High(n);
                double d101 = chartData.Low(n);
                double d102 = 0.5;
                double d103 = 10.0;
                double d104 = SQUtils.round((double)(d100 - d101), (int)this.digits);
                double d105 = SQUtils.round((double)(d96 - d98), (int)this.digits);
                double d106 = d104 != 0.0 ? SQUtils.round((double)(d105 / d104), (int)6) : 0.0;
                double d107 = SQUtils.round((double)((d97 + d99) / 2.0), (int)this.digits);
                double d108 = SQUtils.round((double)(d103 * this.tickSize), (int)this.digits);
                return d99 > d97 && d107 > d98 && d96 > d98 && d98 > d97 && d106 > d102 && d104 >= d108;
            }
            case "Doji": {
                double d109 = SQUtils.round((double)Math.abs(chartData.Open(n) - chartData.Close(n)), (int)this.digits);
                double d110 = SQUtils.round((double)(0.6 * this.tickSize), (int)this.digits);
                return d109 < d110;
            }
            case "Hammer": {
                double d111;
                double d112;
                double d113 = chartData.High(n);
                double d114 = chartData.Low(n);
                double d115 = chartData.Low(n + 1);
                double d116 = chartData.Low(n + 2);
                double d117 = chartData.Low(n + 3);
                double d118 = chartData.Open(n);
                double d119 = chartData.Close(n);
                double d120 = SQUtils.round((double)(d113 - d114), (int)this.digits);
                double d121 = 0.9;
                double d122 = 12.0;
                if (d118 > d119) {
                    d112 = d118;
                    d111 = d119;
                } else {
                    d112 = d119;
                    d111 = d118;
                }
                double d123 = SQUtils.round((double)(d111 - d114), (int)this.digits);
                double d124 = SQUtils.round((double)(d113 - d112), (int)this.digits);
                double d125 = SQUtils.round((double)Math.abs(d118 - d119), (int)this.digits);
                double d126 = SQUtils.round((double)(d125 * d121), (int)this.digits);
                double d127 = SQUtils.round((double)(d123 / 2.0), (int)this.digits);
                double d128 = SQUtils.round((double)(d123 / 3.0), (int)this.digits);
                double d129 = SQUtils.round((double)(d123 / 4.0), (int)this.digits);
                double d130 = SQUtils.round((double)(2.0 * d126), (int)this.digits);
                double d131 = SQUtils.round((double)(d122 * this.tickSize), (int)this.digits);
                if (d114 <= d115 && d114 < d116 && d114 < d117) {
                    if (d127 > d124 && d123 > d130 && d120 >= d131 && d118 != d119 && d128 <= d124 && d129 <= d124) {
                        return true;
                    }
                    if (d128 > d124 && d123 > d130 && d120 >= d131 && d118 != d119 && d129 <= d124) {
                        return true;
                    }
                    if (d129 > d124 && d123 > d130 && d120 >= d131 && d118 != d119) {
                        return true;
                    }
                }
                return false;
            }
            case "PiercingLine": {
                double d132 = chartData.Open(n);
                double d133 = chartData.Open(n + 1);
                double d134 = chartData.Close(n);
                double d135 = chartData.Close(n + 1);
                double d136 = chartData.High(n);
                double d137 = chartData.Low(n);
                double d138 = 0.5;
                double d139 = 10.0;
                double d140 = SQUtils.round((double)(d136 - d137), (int)this.digits);
                double d141 = SQUtils.round((double)(d134 - d132), (int)this.digits);
                double d142 = d140 != 0.0 ? SQUtils.round((double)(d141 / d140), (int)6) : 0.0;
                double d143 = SQUtils.round((double)((d133 + d135) / 2.0), (int)this.digits);
                double d144 = SQUtils.round((double)(d139 * this.tickSize), (int)this.digits);
                return d135 < d133 && d143 < d134 && d132 < d134 && d134 < d133 && d142 > d138 && d140 >= d144;
            }
            case "ShootingStar": {
                double d145;
                double d146;
                double d147 = chartData.High(n);
                double d148 = chartData.Low(n);
                double d149 = chartData.High(n + 1);
                double d150 = chartData.High(n + 2);
                double d151 = chartData.High(n + 3);
                double d152 = chartData.Open(n);
                double d153 = chartData.Close(n);
                double d154 = SQUtils.round((double)(d147 - d148), (int)this.digits);
                double d155 = 0.9;
                double d156 = 12.0;
                if (d152 > d153) {
                    d146 = d152;
                    d145 = d153;
                } else {
                    d146 = d153;
                    d145 = d152;
                }
                double d157 = SQUtils.round((double)(d145 - d148), (int)this.digits);
                double d158 = SQUtils.round((double)(d147 - d146), (int)this.digits);
                double d159 = SQUtils.round((double)Math.abs(d152 - d153), (int)this.digits);
                double d160 = SQUtils.round((double)(d159 * d155), (int)this.digits);
                double d161 = SQUtils.round((double)(d158 / 2.0), (int)this.digits);
                double d162 = SQUtils.round((double)(d158 / 3.0), (int)this.digits);
                double d163 = SQUtils.round((double)(d158 / 4.0), (int)this.digits);
                double d164 = SQUtils.round((double)(2.0 * d160), (int)this.digits);
                double d165 = SQUtils.round((double)(d156 * this.tickSize), (int)this.digits);
                if (d147 >= d149 && d147 > d150 && d147 > d151) {
                    if (d161 > d157 && d158 > d164 && d154 >= d165 && d152 != d153 && d162 <= d157 && d163 <= d157) {
                        return true;
                    }
                    if (d162 > d157 && d158 > d164 && d154 >= d165 && d152 != d153 && d163 <= d157) {
                        return true;
                    }
                    if (d163 > d157 && d158 > d164 && d154 >= d165 && d152 != d153) {
                        return true;
                    }
                }
                return false;
            }
            case "IsBearishFractalUp3": {
                return dataSeries.getRounded(n) > 0.0;
            }
            case "IsBullishFractalDown3": {
                return dataSeries.getRounded(n) > 0.0;
            }
            case "IsBearishFractalUp5": {
                return dataSeries.getRounded(n) > 0.0;
            }
            case "IsBullishFractalDown5": {
                return dataSeries.getRounded(n) > 0.0;
            }
            case "GannHiLoisinDownTrend": {
                double d166 = dataSeries.getRounded(n);
                double d167 = chartData.Close(n);
                return d167 < d166;
            }
            case "GannHiLoisinUpTrend": {
                double d168 = dataSeries.getRounded(n);
                double d169 = chartData.Close(n);
                return d169 > d168;
            }
            case "BarOpenAboveHighestAfterOpenedBelow": {
                double d170 = dataSeries.getRounded(n + 1);
                return chartData.Open(n + 1) < d170 && chartData.Open(n) > d170;
            }
            case "BarOpenAboveLowestAfterOpenedBelow": {
                double d171 = dataSeries.getRounded(n + 1);
                return chartData.Open(n + 1) < d171 && chartData.Open(n) > d171;
            }
            case "BarOpenBelowHighestAfterOpenedAbove": {
                double d172 = dataSeries.getRounded(n + 1);
                return chartData.Open(n + 1) > d172 && chartData.Open(n) < d172;
            }
            case "BarOpenBelowLowestAfterOpenedAbove": {
                double d173 = dataSeries.getRounded(n + 1);
                return chartData.Open(n + 1) > d173 && chartData.Open(n) < d173;
            }
            case "FastHMAisAboveSlowHMA": {
                double d174 = dataSeries.getRounded(n);
                double d175 = dataSeries2.getRounded(n);
                return d174 > d175;
            }
            case "FastHMAisBelowSlowHMA": {
                double d176 = dataSeries.getRounded(n);
                double d177 = dataSeries2.getRounded(n);
                return d176 < d177;
            }
            case "HMAChangedirectionDown": {
                double d178 = dataSeries.getRounded(n + 2);
                double d179 = dataSeries.getRounded(n + 1);
                double d180 = dataSeries.getRounded(n);
                return d178 < d179 && d179 > d180;
            }
            case "HMAChangedirectionUp": {
                double d181 = dataSeries.getRounded(n + 2);
                double d182 = dataSeries.getRounded(n + 1);
                double d183 = dataSeries.getRounded(n);
                return d181 > d182 && d182 < d183;
            }
            case "HMAIsFalling": {
                double d184 = dataSeries.getRounded(n + 1);
                double d185 = dataSeries.getRounded(n);
                return d184 > d185;
            }
            case "HMAIsRising": {
                double d186 = dataSeries.getRounded(n + 1);
                double d187 = dataSeries.getRounded(n);
                return d186 < d187;
            }
            case "IchimokuKijunSenCrossBearish": {
                double d188 = chartData.Open(n);
                double d189 = chartData.Close(n);
                double d190 = dataSeries.getRounded(n);
                boolean bl = d188 > d190 && d189 < d190;
                double d191 = dataSeries2.getRounded(n);
                double d192 = dataSeries3.getRounded(n);
                if (d192 > d191) {
                    double d193 = d192;
                    d192 = d191;
                    d191 = d193;
                }
                int n2 = 1;
                if ((n2 = SQUtils.fixAllowedRange((int)n2, (int)0, (int)2, (int)1)) == 2) {
                    bl = bl && d190 < d192;
                } else if (n2 == 1) {
                    bl = bl && d190 < d191;
                } else if (n2 == 0) {
                    // empty if block
                }
                return bl;
            }
            case "IchimokuKijunSenCrossBullish": {
                double d194 = chartData.Open(n);
                double d195 = chartData.Close(n);
                double d196 = dataSeries.getRounded(n);
                boolean bl = d194 < d196 && d195 > d196;
                double d197 = dataSeries2.getRounded(n);
                double d198 = dataSeries3.getRounded(n);
                if (d198 > d197) {
                    double d199 = d198;
                    d198 = d197;
                    d197 = d199;
                }
                int n3 = 1;
                if ((n3 = SQUtils.fixAllowedRange((int)n3, (int)0, (int)2, (int)1)) == 2) {
                    bl = bl && d196 > d197;
                } else if (n3 == 1) {
                    bl = bl && d196 > d198;
                } else if (n3 == 0) {
                    // empty if block
                }
                return bl;
            }
            case "IchimokuKumoBreakoutBearish": {
                double d200 = chartData.Open(n);
                double d201 = chartData.Close(n);
                double d202 = dataSeries.getRounded(n);
                double d203 = dataSeries2.getRounded(n);
                if (d203 > d202) {
                    double d204 = d203;
                    d203 = d202;
                    d202 = d204;
                }
                boolean bl = d200 > d203 && d201 < d203;
                return bl;
            }
            case "IchimokuKumoBreakoutBullish": {
                double d205 = chartData.Open(n);
                double d206 = chartData.Close(n);
                double d207 = dataSeries.getRounded(n);
                double d208 = dataSeries2.getRounded(n);
                if (d208 > d207) {
                    double d209 = d208;
                    d208 = d207;
                    d207 = d209;
                }
                boolean bl = d205 < d207 && d206 > d207;
                return bl;
            }
            case "IchimokuSenkouSpanCrossBearish": {
                double d210 = dataSeries.getRounded(n + 1);
                double d211 = dataSeries.getRounded(n);
                double d212 = dataSeries2.getRounded(n + 1);
                double d213 = dataSeries2.getRounded(n);
                double d214 = Math.max(d211, d213);
                double d215 = Math.min(d211, d213);
                boolean bl = d210 > d212 && d211 < d213;
                int n4 = 1;
                n4 = SQUtils.fixAllowedRange((int)n4, (int)0, (int)2, (int)1);
                if (n4 == 2) {
                    bl = bl && chartData.Close(n) < d215;
                } else if (n4 == 1) {
                    bl = bl && chartData.Close(n) < d214;
                } else if (n4 == 0) {
                    // empty if block
                }
                return bl;
            }
            case "IchimokuSenkouSpanCrossBullish": {
                double d216 = dataSeries.getRounded(n + 1);
                double d217 = dataSeries.getRounded(n);
                double d218 = dataSeries2.getRounded(n + 1);
                double d219 = dataSeries2.getRounded(n);
                double d220 = Math.max(d217, d219);
                double d221 = Math.min(d217, d219);
                boolean bl = d216 < d218 && d217 > d219;
                int n5 = 1;
                n5 = SQUtils.fixAllowedRange((int)n5, (int)0, (int)2, (int)1);
                if (n5 == 2) {
                    bl = bl && chartData.Close(n) > d220;
                } else if (n5 == 1) {
                    bl = bl && chartData.Close(n) > d221;
                } else if (n5 == 0) {
                    // empty if block
                }
                return bl;
            }
            case "IchimokuTenkanKijunCrossBearish": {
                double d222 = dataSeries.getRounded(n + 1);
                double d223 = dataSeries.getRounded(n);
                double d224 = dataSeries2.getRounded(n + 1);
                double d225 = dataSeries2.getRounded(n);
                double d226 = dataSeries3.getRounded(n);
                double d227 = dataSeries4.getRounded(n);
                if (d227 > d226) {
                    double d228 = d227;
                    d227 = d226;
                    d226 = d228;
                }
                boolean bl = d222 > d224 && d223 < d225;
                int n6 = 1;
                if ((n6 = SQUtils.fixAllowedRange((int)n6, (int)0, (int)2, (int)1)) == 2) {
                    bl = bl && d223 < d227;
                } else if (n6 == 1) {
                    bl = bl && d223 < d226;
                } else if (n6 == 0) {
                    // empty if block
                }
                return bl;
            }
            case "IchimokuTenkanKijunCrossBullish": {
                double d229 = dataSeries.getRounded(n + 1);
                double d230 = dataSeries.getRounded(n);
                double d231 = dataSeries2.getRounded(n + 1);
                double d232 = dataSeries2.getRounded(n);
                double d233 = dataSeries3.getRounded(n);
                double d234 = dataSeries4.getRounded(n);
                if (d234 > d233) {
                    double d235 = d234;
                    d234 = d233;
                    d233 = d235;
                }
                boolean bl = d229 < d231 && d230 > d232;
                int n7 = 1;
                if ((n7 = SQUtils.fixAllowedRange((int)n7, (int)0, (int)2, (int)1)) == 2) {
                    bl = bl && d230 > d233;
                } else if (n7 == 1) {
                    bl = bl && d230 > d234;
                } else if (n7 == 0) {
                    // empty if block
                }
                return bl;
            }
            case "BarCrossesAboveKama": {
                double d236 = dataSeries.getRounded(n);
                double d237 = dataSeries.getRounded(n + 1);
                double d238 = chartData.Close(n);
                double d239 = chartData.Close(n + 1);
                return d236 < d238 && d237 > d239;
            }
            case "BarCrossesBelowKama": {
                double d240 = dataSeries.getRounded(n);
                double d241 = dataSeries.getRounded(n + 1);
                double d242 = chartData.Close(n);
                double d243 = chartData.Close(n + 1);
                return d240 > d242 && d241 < d243;
            }
            case "FastKamaIsAboveSlowKama": {
                double d244 = dataSeries.getRounded(n);
                double d245 = dataSeries2.getRounded(n);
                return d244 > d245;
            }
            case "FastKamaIsBelowSlowKama": {
                double d246 = dataSeries.getRounded(n);
                double d247 = dataSeries2.getRounded(n);
                return d246 < d247;
            }
            case "KamaIsFalling": {
                double d248 = dataSeries.getRounded(n + 1);
                double d249 = dataSeries.getRounded(n);
                return d248 > d249;
            }
            case "KamaIsRising": {
                double d250 = dataSeries.getRounded(n + 1);
                double d251 = dataSeries.getRounded(n);
                return d250 < d251;
            }
            case "KERIsAbove05": {
                double d252 = dataSeries.getRounded(n);
                return d252 > 0.5;
            }
            case "KERIsBelow05": {
                double d253 = dataSeries.getRounded(n);
                return d253 < 0.5;
            }
            case "CloseAboveLowerKC": {
                double d254 = dataSeries.getRounded(n);
                return chartData.Close(n) > d254;
            }
            case "CloseAboveUpperKC": {
                double d255 = dataSeries.getRounded(n);
                return chartData.Close(n) > d255;
            }
            case "CloseBelowLowerKC": {
                double d256 = dataSeries.getRounded(n);
                return chartData.Close(n) < d256;
            }
            case "CloseBelowUpperKC": {
                double d257 = dataSeries.getRounded(n);
                return chartData.Close(n) < d257;
            }
            case "OpenAboveLowerKC": {
                double d258 = dataSeries.getRounded(n + 1);
                return chartData.Open(n) > d258;
            }
            case "OpenAboveUpperKC": {
                double d259 = dataSeries.getRounded(n + 1);
                return chartData.Open(n) > d259;
            }
            case "OpenBelowLowerKC": {
                double d260 = dataSeries.getRounded(n + 1);
                return chartData.Open(n) < d260;
            }
            case "OpenBelowUpperKC": {
                double d261 = dataSeries.getRounded(n + 1);
                return chartData.Open(n) < d261;
            }
            case "OpenAboveLowerKCAfterOpenedBelow": {
                double d262 = dataSeries.getRounded(n + 1);
                return chartData.Open(n + 1) < d262 && chartData.Open(n) > d262;
            }
            case "OpenAboveUpperKCAfterOpenedBelow": {
                double d263 = dataSeries.getRounded(n + 1);
                return chartData.Open(n + 1) < d263 && chartData.Open(n) > d263;
            }
            case "OpenBelowLowerKCAfterOpenedAbove": {
                double d264 = dataSeries.getRounded(n + 1);
                return chartData.Open(n + 1) > d264 && chartData.Open(n) < d264;
            }
            case "OpenBelowUpperKCAfterOpenedAbove": {
                double d265 = dataSeries.getRounded(n + 1);
                return chartData.Open(n + 1) > d265 && chartData.Open(n) < d265;
            }
            case "KCLowerIsFalling": {
                double d266 = dataSeries.getRounded(n + 1);
                double d267 = dataSeries.getRounded(n);
                return d266 > d267;
            }
            case "KCLowerIsRising": {
                double d268 = dataSeries.getRounded(n + 1);
                double d269 = dataSeries.getRounded(n);
                return d268 < d269;
            }
            case "KCUpperIsFalling": {
                double d270 = dataSeries.getRounded(n + 1);
                double d271 = dataSeries.getRounded(n);
                return d270 > d271;
            }
            case "KCUpperIsRising": {
                double d272 = dataSeries.getRounded(n + 1);
                double d273 = dataSeries.getRounded(n);
                return d272 < d273;
            }
            case "LaguerreRSI05ChangeDirectionDown": {
                double d274 = dataSeries.getRounded(n);
                double d275 = dataSeries.getRounded(n + 1);
                double d276 = dataSeries.getRounded(n + 2);
                return d274 < d275 && d276 < d275;
            }
            case "LaguerreRSI05ChangeDirectionUp": {
                double d277 = dataSeries.getRounded(n);
                double d278 = dataSeries.getRounded(n + 1);
                double d279 = dataSeries.getRounded(n + 2);
                return d277 > d278 && d279 > d278;
            }
            case "LaguerreRSI05CrossAbove05": {
                double d280 = dataSeries.getRounded(n);
                double d281 = dataSeries.getRounded(n + 1);
                return d280 > 0.5 && d281 < 0.5;
            }
            case "LaguerreRSI05CrossBelow05": {
                double d282 = dataSeries.getRounded(n);
                double d283 = dataSeries.getRounded(n + 1);
                return d282 < 0.5 && d283 > 0.5;
            }
            case "LaguerreRSI05IsFalling": {
                double d284 = dataSeries.getRounded(n);
                double d285 = dataSeries.getRounded(n + 1);
                return d284 < d285;
            }
            case "LaguerreRSI05IsRising": {
                double d286 = dataSeries.getRounded(n);
                double d287 = dataSeries.getRounded(n + 1);
                return d286 > d287;
            }
            case "LinRegCloseAbove": {
                double d288 = dataSeries.getRounded(n);
                return chartData.Close(n) > d288;
            }
            case "LinRegCloseBelow": {
                double d289 = dataSeries.getRounded(n);
                return chartData.Close(n) < d289;
            }
            case "LinRegOpenAbove": {
                double d290 = dataSeries.getRounded(n + 1);
                return chartData.Open(n) > d290;
            }
            case "LinRegOpenBelow": {
                double d291 = dataSeries.getRounded(n + 1);
                return chartData.Open(n) < d291;
            }
            case "LinRegOpenAboveAfterOpenedBelow": {
                double d292 = dataSeries.getRounded(n + 1);
                return chartData.Open(n + 1) < d292 && chartData.Open(n) > d292;
            }
            case "LinRegOpenBelowAfterOpenedAbove": {
                double d293 = dataSeries.getRounded(n + 1);
                return chartData.Open(n + 1) > d293 && chartData.Open(n) < d293;
            }
            case "LinRegIsFalling": {
                double d294 = dataSeries.getRounded(n + 1);
                double d295 = dataSeries.getRounded(n);
                return d294 > d295;
            }
            case "LinRegIsRising": {
                double d296 = dataSeries.getRounded(n + 1);
                double d297 = dataSeries.getRounded(n);
                return d296 < d297;
            }
            case "MACDChangeDirectionDown": {
                double d298 = dataSeries.getRounded(n + 2);
                double d299 = dataSeries.getRounded(n + 1);
                double d300 = dataSeries.getRounded(n);
                return d298 < d299 && d299 > d300;
            }
            case "MACDChangeDirectionUP": {
                double d301 = dataSeries.getRounded(n + 2);
                double d302 = dataSeries.getRounded(n + 1);
                double d303 = dataSeries.getRounded(n);
                return d301 > d302 && d302 < d303;
            }
            case "MACDCrossAbove0": {
                double d304 = dataSeries.getRounded(n + 1);
                double d305 = dataSeries.getRounded(n);
                return d304 < 0.0 && d305 > 0.0;
            }
            case "MACDCrossAbove001": {
                double d306 = dataSeries.getRounded(n + 1);
                double d307 = dataSeries.getRounded(n);
                return d306 < 0.01 && d307 > 0.01;
            }
            case "MACDCrossAboveSignal": {
                double d308 = dataSeries.getRounded(n + 1);
                double d309 = dataSeries.getRounded(n);
                double d310 = dataSeries2.getRounded(n + 1);
                double d311 = dataSeries2.getRounded(n);
                return d308 < d310 && d309 > d311;
            }
            case "MACDCrossbelow0": {
                double d312 = dataSeries.getRounded(n + 1);
                double d313 = dataSeries.getRounded(n);
                return d312 > 0.0 && d313 < 0.0;
            }
            case "MACDCrossbelow001": {
                double d314 = dataSeries.getRounded(n + 1);
                double d315 = dataSeries.getRounded(n);
                return d314 > 0.01 && d315 < 0.01;
            }
            case "MACDCrossbelowSignal": {
                double d316 = dataSeries.getRounded(n + 1);
                double d317 = dataSeries.getRounded(n);
                double d318 = dataSeries2.getRounded(n + 1);
                double d319 = dataSeries2.getRounded(n);
                return d316 > d318 && d317 < d319;
            }
            case "MACDMainIsFalling": {
                double d320 = dataSeries.getRounded(n + 1);
                double d321 = dataSeries.getRounded(n);
                return d320 > d321;
            }
            case "MACDMainIsRising": {
                double d322 = dataSeries.getRounded(n + 1);
                double d323 = dataSeries.getRounded(n);
                return d322 < d323;
            }
            case "MACDSignalIsFalling": {
                double d324 = dataSeries2.getRounded(n + 1);
                double d325 = dataSeries2.getRounded(n);
                return d324 > d325;
            }
            case "MACDSignalIsRising": {
                double d326 = dataSeries2.getRounded(n + 1);
                double d327 = dataSeries2.getRounded(n);
                return d326 < d327;
            }
            case "MACDMainIsHigherThan0": {
                double d328 = dataSeries.getRounded(n);
                return d328 > 0.0;
            }
            case "MACDMainIsHigherThanLevel001": {
                double d329 = dataSeries.getRounded(n);
                return d329 > 0.01;
            }
            case "MACDMainIsHigherThanSignal": {
                double d330 = dataSeries.getRounded(n);
                double d331 = dataSeries2.getRounded(n);
                return d330 > d331;
            }
            case "MACDMainIsLowerThan0": {
                double d332 = dataSeries.getRounded(n);
                return d332 < 0.0;
            }
            case "MACDMainIsLowerThanLevel001": {
                double d333 = dataSeries.getRounded(n);
                return d333 < 0.01;
            }
            case "MACDMainIsLowerThanSignal": {
                double d334 = dataSeries.getRounded(n);
                double d335 = dataSeries2.getRounded(n);
                return d334 < d335;
            }
            case "MomentumChangeDirectionDown": {
                double d336 = dataSeries.getRounded(n + 2);
                double d337 = dataSeries.getRounded(n + 1);
                double d338 = dataSeries.getRounded(n);
                return d336 < d337 && d337 > d338;
            }
            case "MomentumChangeDirectionUp": {
                double d339 = dataSeries.getRounded(n + 2);
                double d340 = dataSeries.getRounded(n + 1);
                double d341 = dataSeries.getRounded(n);
                return d339 > d340 && d340 < d341;
            }
            case "MomentumCrossAbove0": {
                double d342 = dataSeries.getRounded(n + 1);
                double d343 = dataSeries.getRounded(n);
                return d342 < 0.0 && d343 > 0.0;
            }
            case "MomentumCrossBelow0": {
                double d344 = dataSeries.getRounded(n + 1);
                double d345 = dataSeries.getRounded(n);
                return d344 > 0.0 && d345 < 0.0;
            }
            case "MomentumIsFalling": {
                double d346 = dataSeries.getRounded(n + 1);
                double d347 = dataSeries.getRounded(n);
                return d346 > d347;
            }
            case "MomentumIsRising": {
                double d348 = dataSeries.getRounded(n + 1);
                double d349 = dataSeries.getRounded(n);
                return d348 < d349;
            }
            case "MomentumIsGreater": {
                double d350 = dataSeries.getRounded(n);
                return d350 > 0.0;
            }
            case "MomentumIsLower": {
                double d351 = dataSeries.getRounded(n);
                return d351 < 0.0;
            }
            case "BarClosesAboveMovingAverage": {
                return dataSeries.getRounded(n) < chartData.Close(n);
            }
            case "BarClosesBelowMovingAverage": {
                return dataSeries.getRounded(n) > chartData.Close(n);
            }
            case "BarOpenAboveMovingAverage": {
                return dataSeries.getRounded(n + 1) < chartData.Open(n);
            }
            case "BarOpenBelowMovingAverage": {
                return dataSeries.getRounded(n + 1) > chartData.Open(n);
            }
            case "BarOpensAboveAfterOpenBelowMovingAverage": {
                return chartData.Open(n + 1) < dataSeries.getRounded(n + 1) && chartData.Open(n) > dataSeries.getRounded(n + 1);
            }
            case "BarOpensBelowAfterOpenAboveMovingAverage": {
                return chartData.Open(n + 1) > dataSeries.getRounded(n + 1) && chartData.Open(n) < dataSeries.getRounded(n + 1);
            }
            case "MovingAverageFalling": {
                return dataSeries.getRounded(n) < dataSeries.getRounded(n + 1);
            }
            case "MovingAverageRising": {
                return dataSeries.getRounded(n) > dataSeries.getRounded(n + 1);
            }
            case "OSMAChangeDirectionDown": {
                double d352 = dataSeries.getRounded(n + 2);
                double d353 = dataSeries.getRounded(n + 1);
                double d354 = dataSeries.getRounded(n);
                return d352 < d353 && d353 > d354;
            }
            case "OSMAChangeDirectionUp": {
                double d355 = dataSeries.getRounded(n + 2);
                double d356 = dataSeries.getRounded(n + 1);
                double d357 = dataSeries.getRounded(n);
                return d355 > d356 && d356 < d357;
            }
            case "OSMACrossAbove0": {
                double d358 = dataSeries.getRounded(n + 1);
                double d359 = dataSeries.getRounded(n);
                return d358 < 0.0 && d359 > 0.0;
            }
            case "OSMACrossBelow0": {
                double d360 = dataSeries.getRounded(n + 1);
                double d361 = dataSeries.getRounded(n);
                return d360 > 0.0 && d361 < 0.0;
            }
            case "OSMAIsFalling": {
                double d362 = dataSeries.getRounded(n + 1);
                double d363 = dataSeries.getRounded(n);
                return d362 > d363;
            }
            case "OSMAIsRising": {
                double d364 = dataSeries.getRounded(n + 1);
                double d365 = dataSeries.getRounded(n);
                return d364 < d365;
            }
            case "OSMAIsGreater0": {
                double d366 = dataSeries.getRounded(n);
                return d366 > 0.0;
            }
            case "OSMAIsLower0": {
                double d367 = dataSeries.getRounded(n);
                return d367 < 0.0;
            }
            case "PriceAbovePSAR": {
                return chartData.Close(n) > dataSeries.getRounded(n + 1);
            }
            case "PriceBelowPSAR": {
                return chartData.Close(n) < dataSeries.getRounded(n + 1);
            }
            case "QQEChangeDirectionDown": {
                double d368 = dataSeries.getRounded(n + 2);
                double d369 = dataSeries.getRounded(n + 1);
                double d370 = dataSeries.getRounded(n);
                return d368 < d369 && d369 > d370;
            }
            case "QQEChangeDirectionUP": {
                double d371 = dataSeries.getRounded(n + 2);
                double d372 = dataSeries.getRounded(n + 1);
                double d373 = dataSeries.getRounded(n);
                return d371 > d372 && d372 < d373;
            }
            case "QQEIsGreater0": {
                double d374 = dataSeries.getRounded(n);
                return d374 > 0.0;
            }
            case "QQEIsLower0": {
                double d375 = dataSeries.getRounded(n);
                return d375 < 0.0;
            }
            case "QQEVal1CrossAbove0": {
                double d376 = dataSeries.getRounded(n + 1);
                double d377 = dataSeries.getRounded(n);
                return d376 < 0.0 && d377 > 0.0;
            }
            case "QQEVal1CrossBelow0": {
                double d378 = dataSeries.getRounded(n + 1);
                double d379 = dataSeries.getRounded(n);
                return d378 > 0.0 && d379 < 0.0;
            }
            case "QQEVal1CrossAboveVal2": {
                double d380 = dataSeries.getRounded(n + 1);
                double d381 = dataSeries.getRounded(n);
                double d382 = dataSeries2.getRounded(n + 1);
                double d383 = dataSeries2.getRounded(n);
                return d380 < d382 && d381 > d383;
            }
            case "QQEVal1CrossBelowVal2": {
                double d384 = dataSeries.getRounded(n + 1);
                double d385 = dataSeries.getRounded(n);
                double d386 = dataSeries2.getRounded(n + 1);
                double d387 = dataSeries2.getRounded(n);
                return d384 > d386 && d385 < d387;
            }
            case "QQEVal1IsFalling": {
                double d388 = dataSeries.getRounded(n + 1);
                double d389 = dataSeries.getRounded(n);
                return d388 > d389;
            }
            case "QQEVal1IsRising": {
                double d390 = dataSeries.getRounded(n + 1);
                double d391 = dataSeries.getRounded(n);
                return d390 < d391;
            }
            case "QQEVal2IsFalling": {
                double d392 = dataSeries.getRounded(n + 1);
                double d393 = dataSeries.getRounded(n);
                return d392 > d393;
            }
            case "QQEVal2IsRising": {
                double d394 = dataSeries.getRounded(n + 1);
                double d395 = dataSeries.getRounded(n);
                return d394 < d395;
            }
            case "QQEVal2IsGreaterVal1": {
                double d396 = dataSeries.getRounded(n);
                double d397 = dataSeries2.getRounded(n);
                return d396 < d397;
            }
            case "QQEVal1IsGreaterVal2": {
                double d398 = dataSeries.getRounded(n);
                double d399 = dataSeries2.getRounded(n);
                return d398 > d399;
            }
            case "FastReflexCrossDownSlowReflex": {
                double d400 = dataSeries.getRounded(n);
                double d401 = dataSeries2.getRounded(n);
                double d402 = dataSeries.getRounded(n + 1);
                double d403 = dataSeries2.getRounded(n + 1);
                return d400 < d401 & d402 > d403;
            }
            case "FastReflexCrossUpSlowReflex": {
                double d404 = dataSeries.getRounded(n);
                double d405 = dataSeries2.getRounded(n);
                double d406 = dataSeries.getRounded(n + 1);
                double d407 = dataSeries2.getRounded(n + 1);
                return d404 > d405 & d406 < d407;
            }
            case "ReflexChangeDirectionDown": {
                double d408 = dataSeries.getRounded(n);
                double d409 = dataSeries.getRounded(n + 1);
                double d410 = dataSeries.getRounded(n + 2);
                double d411 = dataSeries.getRounded(n + 3);
                return d408 < d409 && d410 < d409 || d408 < d409 && d411 < d410;
            }
            case "ReflexChangeDirectionUp": {
                double d412 = dataSeries.getRounded(n);
                double d413 = dataSeries.getRounded(n + 1);
                double d414 = dataSeries.getRounded(n + 2);
                double d415 = dataSeries.getRounded(n + 3);
                return d412 > d413 && d414 > d413 || d412 > d413 && d415 > d414;
            }
            case "ReflexIsFalling": {
                double d416 = dataSeries.getRounded(n + 1);
                double d417 = dataSeries.getRounded(n);
                return d417 < d416;
            }
            case "ReflexIsRising": {
                double d418 = dataSeries.getRounded(n + 1);
                double d419 = dataSeries.getRounded(n);
                return d419 > d418;
            }
            case "ROCCrossAbove0": {
                double d420 = dataSeries.getRounded(n);
                double d421 = dataSeries.getRounded(n + 1);
                return d420 > 0.0 && d421 < 0.0;
            }
            case "ROCCrossBelow0": {
                double d422 = dataSeries.getRounded(n);
                double d423 = dataSeries.getRounded(n + 1);
                return d422 < 0.0 && d423 > 0.0;
            }
            case "ROCIsAbove0": {
                double d424 = dataSeries.getRounded(n);
                return d424 > 0.0;
            }
            case "ROCIsBelow0": {
                double d425 = dataSeries.getRounded(n);
                return d425 < 0.0;
            }
            case "ROCIsFalling": {
                double d426 = dataSeries.getRounded(n);
                double d427 = dataSeries.getRounded(n + 1);
                return d426 < d427;
            }
            case "ROCIsRising": {
                double d428 = dataSeries.getRounded(n);
                double d429 = dataSeries.getRounded(n + 1);
                return d428 > d429;
            }
            case "RSIChangeDirectionDown": {
                double d430 = dataSeries.getRounded(n + 2);
                double d431 = dataSeries.getRounded(n + 1);
                double d432 = dataSeries.getRounded(n);
                return d430 < d431 && d431 > d432;
            }
            case "RSIChangeDirectionUp": {
                double d433 = dataSeries.getRounded(n + 2);
                double d434 = dataSeries.getRounded(n + 1);
                double d435 = dataSeries.getRounded(n);
                return d433 > d434 && d434 < d435;
            }
            case "RSICrossAbove0": {
                double d436 = dataSeries.getRounded(n + 1);
                double d437 = dataSeries.getRounded(n);
                return d436 < 0.0 && d437 > 0.0;
            }
            case "RSICrossBelow0": {
                double d438 = dataSeries.getRounded(n + 1);
                double d439 = dataSeries.getRounded(n);
                return d438 > 0.0 && d439 < 0.0;
            }
            case "RSIGreater0": {
                double d440 = dataSeries.getRounded(n);
                return d440 > 0.0;
            }
            case "RSILower0": {
                double d441 = dataSeries.getRounded(n);
                return d441 < 0.0;
            }
            case "RSIIsFalling": {
                double d442 = dataSeries.getRounded(n + 1);
                double d443 = dataSeries.getRounded(n);
                return d442 > d443;
            }
            case "RSIIsRising": {
                double d444 = dataSeries.getRounded(n + 1);
                double d445 = dataSeries.getRounded(n);
                return d444 < d445;
            }
            case "SchaffTrendCycleAbove80": {
                double d446 = dataSeries.getRounded(n);
                double d447 = 80.0;
                return d446 > d447;
            }
            case "SchaffTrendCycleBelow20": {
                double d448 = dataSeries.getRounded(n);
                double d449 = 20.0;
                return d448 < d449;
            }
            case "SchaffTrendCycleCrossAbove80": {
                double d450 = dataSeries.getRounded(n);
                double d451 = dataSeries.getRounded(n + 1);
                return d450 > 80.0 && d451 < 80.0;
            }
            case "SchaffTrendCycleCrossBelow20": {
                double d452 = dataSeries.getRounded(n);
                double d453 = dataSeries.getRounded(n + 1);
                return d452 < 20.0 && d453 > 20.0;
            }
            case "SRPercentRankAbove80": {
                double d454 = dataSeries.getRounded(n);
                return d454 > 80.0;
            }
            case "SRPercentRankBelow20": {
                double d455 = dataSeries.getRounded(n);
                return d455 < 20.0;
            }
            case "SRPercentRankAbove80for2bars": {
                boolean bl = false;
                for (int i = 0; i < 2; ++i) {
                    if (dataSeries.getRounded(n + i, 5) < 80.0) {
                        return false;
                    }
                    if (!(dataSeries.getRounded(n + i, 5) > 80.0)) continue;
                    bl = true;
                }
                return bl;
            }
            case "SRPercentRankBelow20for2bars": {
                boolean bl = false;
                for (int i = 0; i < 2; ++i) {
                    if (dataSeries.getRounded(n + i, 5) > 20.0) {
                        return false;
                    }
                    if (!(dataSeries.getRounded(n + i, 5) < 20.0)) continue;
                    bl = true;
                }
                return bl;
            }
            case "StdDevChangeDirectionDown": {
                double d456 = dataSeries.getRounded(n + 2);
                double d457 = dataSeries.getRounded(n + 1);
                double d458 = dataSeries.getRounded(n);
                return d456 < d457 && d457 > d458;
            }
            case "StdDevChangeDirectionUp": {
                double d459 = dataSeries.getRounded(n + 2);
                double d460 = dataSeries.getRounded(n + 1);
                double d461 = dataSeries.getRounded(n);
                return d459 > d460 && d460 < d461;
            }
            case "StdDevCrossAbove": {
                double d462 = dataSeries.getRounded(n + 1);
                double d463 = dataSeries.getRounded(n);
                return d462 < 1.0E-4 && d463 > 1.0E-4;
            }
            case "StdDevCrossBelow": {
                double d464 = dataSeries.getRounded(n + 1);
                double d465 = dataSeries.getRounded(n);
                return d464 > 1.0E-4 && d465 < 1.0E-4;
            }
            case "StdDevIsFalling": {
                double d466 = dataSeries.getRounded(n + 1);
                double d467 = dataSeries.getRounded(n);
                return d466 > d467;
            }
            case "StdDevIsRising": {
                double d468 = dataSeries.getRounded(n + 1);
                double d469 = dataSeries.getRounded(n);
                return d468 < d469;
            }
            case "StdDevIsHigher": {
                double d470 = dataSeries.getRounded(n);
                return d470 > 1.0E-4;
            }
            case "StdDevIsLower": {
                double d471 = dataSeries.getRounded(n);
                return d471 < 1.0E-4;
            }
            case "StochasticFastKCrossAbove": {
                double d472 = dataSeries.getRounded(n + 1);
                double d473 = dataSeries.getRounded(n);
                return d472 < 50.0 && d473 > 50.0;
            }
            case "StochasticFastKCrossBelow": {
                double d474 = dataSeries.getRounded(n + 1);
                double d475 = dataSeries.getRounded(n);
                return d474 > 50.0 && d475 < 50.0;
            }
            case "StochasticFastKHigherSlowD": {
                double d476 = dataSeries2.getRounded(n);
                double d477 = dataSeries.getRounded(n);
                return d476 > d477;
            }
            case "StochasticFastKLowerSlowD": {
                double d478 = dataSeries2.getRounded(n);
                double d479 = dataSeries.getRounded(n);
                return d478 < d479;
            }
            case "StochasticSlowDChangeDownwards": {
                double d480 = dataSeries.getRounded(n + 2);
                double d481 = dataSeries.getRounded(n + 1);
                double d482 = dataSeries.getRounded(n);
                return d480 < d481 && d481 > d482;
            }
            case "StochasticSlowDChangeUpwards": {
                double d483 = dataSeries.getRounded(n + 2);
                double d484 = dataSeries.getRounded(n + 1);
                double d485 = dataSeries.getRounded(n);
                return d483 > d484 && d484 < d485;
            }
            case "StochasticSlowDCrossAbove": {
                double d486 = dataSeries.getRounded(n + 1);
                double d487 = dataSeries.getRounded(n);
                return d486 < 50.0 && d487 > 50.0;
            }
            case "StochasticSlowDCrossBelow": {
                double d488 = dataSeries.getRounded(n + 1);
                double d489 = dataSeries.getRounded(n);
                return d488 > 50.0 && d489 < 50.0;
            }
            case "StochasticSlowDIsFalling": {
                double d490 = dataSeries.getRounded(n + 1);
                double d491 = dataSeries.getRounded(n);
                return d490 > d491;
            }
            case "StochasticSlowDIsRising": {
                double d492 = dataSeries.getRounded(n + 1);
                double d493 = dataSeries.getRounded(n);
                return d492 < d493;
            }
            case "StochasticSlowDIsHigher": {
                double d494 = dataSeries.getRounded(n);
                return d494 > 50.0;
            }
            case "StochasticSlowDIsLower": {
                double d495 = dataSeries.getRounded(n);
                return d495 < 50.0;
            }
            case "SuperTrendCloseAbove": {
                double d496 = dataSeries.getRounded(n);
                double d497 = chartData.Close.get(n);
                return d497 > d496;
            }
            case "SuperTrendCloseBelow": {
                double d498 = dataSeries.getRounded(n);
                double d499 = chartData.Close.get(n);
                return d499 < d498;
            }
            case "SuperTrendIsFalling": {
                double d500 = dataSeries.getRounded(n);
                double d501 = dataSeries.getRounded(n + 1);
                return d500 < d501;
            }
            case "SuperTrendIsRising": {
                double d502 = dataSeries.getRounded(n);
                double d503 = dataSeries.getRounded(n + 1);
                return d502 > d503;
            }
            case "SuperTrendIsInRange": {
                double d504 = dataSeries.getRounded(n, 5);
                double d505 = dataSeries.getRounded(n + 1, 5);
                return d504 == d505;
            }
            case "IsDownTrend": {
                double d506 = dataSeries.getRounded(n);
                double d507 = chartData.Close(n);
                return d507 < d506;
            }
            case "IsUpTrend": {
                double d508 = dataSeries.getRounded(n);
                double d509 = chartData.Close(n);
                return d509 > d508;
            }
            case "UlcerIndexDownIsBelow": {
                double d510 = dataSeries.getRounded(n);
                return d510 < 0.2;
            }
            case "UlcerIndexUpIsBelow": {
                double d511 = dataSeries.getRounded(n);
                return d511 < 0.2;
            }
            case "UlcerIndexDownIsRising": {
                double d512 = dataSeries.getRounded(n);
                double d513 = dataSeries.getRounded(n + 1);
                return d512 > d513;
            }
            case "UlcerIndexUpIsRising": {
                double d514 = dataSeries.getRounded(n);
                double d515 = dataSeries.getRounded(n + 1);
                return d514 > d515;
            }
            case "VortexIsDownTrend": {
                double d516 = dataSeries.getRounded(n);
                double d517 = dataSeries2.getRounded(n);
                return d516 < d517;
            }
            case "VortexIsUpTrend": {
                double d518 = dataSeries.getRounded(n);
                double d519 = dataSeries2.getRounded(n);
                return d518 > d519;
            }
            case "VortexChangeTrendDown": {
                double d520 = dataSeries.getRounded(n);
                double d521 = dataSeries.getRounded(n + 1);
                double d522 = dataSeries2.getRounded(n);
                double d523 = dataSeries2.getRounded(n + 1);
                return d520 < d522 && d521 > d523;
            }
            case "VortexChangeTrendUp": {
                double d524 = dataSeries.getRounded(n);
                double d525 = dataSeries.getRounded(n + 1);
                double d526 = dataSeries2.getRounded(n);
                double d527 = dataSeries2.getRounded(n + 1);
                return d524 > d526 && d525 < d527;
            }
            case "CloseIsAboveVWAP": {
                double d528 = dataSeries.getRounded(n);
                double d529 = chartData.Close.get(n);
                return d528 < d529;
            }
            case "CloseIsBelowVWAP": {
                double d530 = dataSeries.getRounded(n);
                double d531 = chartData.Close.get(n);
                return d531 < d530;
            }
            case "FasterVWAPIsAboveSlowerVWAP": {
                double d532 = dataSeries.getRounded(n);
                double d533 = dataSeries2.getRounded(n);
                return d532 > d533;
            }
            case "FasterVWAPIsBelowSlowerVWAP": {
                double d534 = dataSeries.getRounded(n);
                double d535 = dataSeries2.getRounded(n);
                return d534 < d535;
            }
            case "VWAPIsFalling": {
                double d536 = dataSeries.getRounded(n);
                double d537 = dataSeries.getRounded(n + 1);
                return d536 < d537;
            }
            case "VWAPIsRising": {
                double d538 = dataSeries.getRounded(n);
                double d539 = dataSeries.getRounded(n + 1);
                return d538 > d539;
            }
            case "WilliamPRChangeDown": {
                double d540 = dataSeries.getRounded(n + 2);
                double d541 = dataSeries.getRounded(n + 1);
                double d542 = dataSeries.getRounded(n);
                return d540 < d541 && d541 > d542;
            }
            case "WilliamPRChangeUP": {
                double d543 = dataSeries.getRounded(n + 2);
                double d544 = dataSeries.getRounded(n + 1);
                double d545 = dataSeries.getRounded(n);
                return d543 > d544 && d544 < d545;
            }
            case "WilliamPRCrossAbove-50": {
                double d546 = dataSeries.getRounded(n + 1);
                double d547 = dataSeries.getRounded(n);
                return d546 < -50.0 && d547 > -50.0;
            }
            case "WilliamPRCrossBelow-50": {
                double d548 = dataSeries.getRounded(n + 1);
                double d549 = dataSeries.getRounded(n);
                return d548 > -50.0 && d549 < -50.0;
            }
            case "WilliamPRIsAbove-50": {
                double d550 = dataSeries.getRounded(n);
                return d550 > -50.0;
            }
            case "WilliamPRIsBelow-50": {
                double d551 = dataSeries.getRounded(n);
                return d551 < -50.0;
            }
            case "WilliamPRIsFalling": {
                double d552 = dataSeries.getRounded(n + 1);
                double d553 = dataSeries.getRounded(n);
                return d552 > d553;
            }
            case "WilliamPRIsRising": {
                double d554 = dataSeries.getRounded(n + 1);
                double d555 = dataSeries.getRounded(n);
                return d554 < d555;
            }
            case "WaveTrendChangeDirectionDown": {
                double d556 = dataSeries.getRounded(n + 2);
                double d557 = dataSeries.getRounded(n + 1);
                double d558 = dataSeries.getRounded(n);
                return d556 < d557 && d557 > d558;
            }
            case "WaveTrendChangeDirectionUP": {
                double d559 = dataSeries.getRounded(n + 2);
                double d560 = dataSeries.getRounded(n + 1);
                double d561 = dataSeries.getRounded(n);
                return d559 > d560 && d560 < d561;
            }
            case "WaveTrendCrossAbove0": {
                double d562 = dataSeries.getRounded(n + 1);
                double d563 = dataSeries.getRounded(n);
                return d562 < 0.0 && d563 > 0.0;
            }
            case "WaveTrendCrossAbove001": {
                double d564 = dataSeries.getRounded(n + 1);
                double d565 = dataSeries.getRounded(n);
                return d564 < 0.01 && d565 > 0.01;
            }
            case "WaveTrendCrossAboveSignal": {
                double d566 = dataSeries.getRounded(n + 1);
                double d567 = dataSeries.getRounded(n);
                double d568 = dataSeries2.getRounded(n + 1);
                double d569 = dataSeries2.getRounded(n);
                return d566 < d568 && d567 > d569;
            }
            case "WaveTrendCrossbelow0": {
                double d570 = dataSeries.getRounded(n + 1);
                double d571 = dataSeries.getRounded(n);
                return d570 > 0.0 && d571 < 0.0;
            }
            case "WaveTrendCrossbelow001": {
                double d572 = dataSeries.getRounded(n + 1);
                double d573 = dataSeries.getRounded(n);
                return d572 > 0.01 && d573 < 0.01;
            }
            case "WaveTrendCrossbelowSignal": {
                double d574 = dataSeries.getRounded(n + 1);
                double d575 = dataSeries.getRounded(n);
                double d576 = dataSeries2.getRounded(n + 1);
                double d577 = dataSeries2.getRounded(n);
                return d574 > d576 && d575 < d577;
            }
            case "WaveTrendMainIsFalling": {
                double d578 = dataSeries.getRounded(n + 1);
                double d579 = dataSeries.getRounded(n);
                return d578 > d579;
            }
            case "WaveTrendMainIsRising": {
                double d580 = dataSeries.getRounded(n + 1);
                double d581 = dataSeries.getRounded(n);
                return d580 < d581;
            }
            case "WaveTrendSignalIsFalling": {
                double d582 = dataSeries2.getRounded(n + 1);
                double d583 = dataSeries2.getRounded(n);
                return d582 > d583;
            }
            case "WaveTrendSignalIsRising": {
                double d584 = dataSeries2.getRounded(n + 1);
                double d585 = dataSeries2.getRounded(n);
                return d584 < d585;
            }
            case "WaveTrendMainIsHigherThan0": {
                double d586 = dataSeries.getRounded(n);
                return d586 > 0.0;
            }
            case "WaveTrendMainIsHigherThanLevel001": {
                double d587 = dataSeries.getRounded(n);
                return d587 > 0.01;
            }
            case "WaveTrendMainIsHigherThanSignal": {
                double d588 = dataSeries.getRounded(n);
                double d589 = dataSeries2.getRounded(n);
                return d588 > d589;
            }
            case "WaveTrendMainIsLowerThan0": {
                double d590 = dataSeries.getRounded(n);
                return d590 < 0.0;
            }
            case "WaveTrendMainIsLowerThanLevel001": {
                double d591 = dataSeries.getRounded(n);
                return d591 < 0.01;
            }
            case "WaveTrendMainIsLowerThanSignal": {
                double d592 = dataSeries.getRounded(n);
                double d593 = dataSeries2.getRounded(n);
                return d592 < d593;
            }
        }
        return false;
    }

    public String getFilePath(String string) {
        return this.indicatorTestsPath + "/" + this.engine + "/" + string;
    }

    private boolean checkPrecision(double d, double d2, int n) {
        double d3 = Math.pow(10.0, -n);
        return Math.abs(d - d2) < d3;
    }

    private ChartData loadSourceData(String string, DataSeries dataSeries) throws Exception {
        InstrumentInfo instrumentInfo;
        ArrayList arrayList = SQUtils.loadLines((String)string, (String)";");
        TimeDataSeries timeDataSeries = new TimeDataSeries();
        DataSeries dataSeries2 = new DataSeries();
        DataSeries dataSeries3 = new DataSeries();
        DataSeries dataSeries4 = new DataSeries();
        DataSeries dataSeries5 = new DataSeries();
        DataSeries dataSeries6 = new DataSeries();
        this.tfRecognizer.reset();
        int n = 0;
        for (int i = 0; i < arrayList.size(); ++i) {
            instrumentInfo = (InstrumentInfo)arrayList.get(i);
            if (((String[])instrumentInfo).length < 7) {
                if (++n >= this.maxInvalidLines) continue;
                String string2 = "Parse error - Invalid line no." + (i + 1) + ". Expected 7 values, got " + ((String[])instrumentInfo).length + ".";
                this.dataErrors.add(string2);
                Log.error(string2);
                continue;
            }
            try {
                long l = this.df.parse(instrumentInfo[0]).getTime();
                timeDataSeries.add(l);
                dataSeries2.add(Double.parseDouble(instrumentInfo[1].trim()));
                dataSeries3.add(Double.parseDouble(instrumentInfo[2].trim()));
                dataSeries4.add(Double.parseDouble(instrumentInfo[3].trim()));
                dataSeries5.add(Double.parseDouble(instrumentInfo[4].trim()));
                dataSeries6.add(Double.parseDouble(instrumentInfo[5].trim()));
                dataSeries.add(Double.parseDouble(instrumentInfo[6].trim()));
                this.tfRecognizer.processTime(l);
                continue;
            }
            catch (Exception exception) {
                if (++n >= this.maxInvalidLines) continue;
                String string3 = "Parse error - Invalid line no." + (i + 1) + ". " + exception.getMessage();
                this.dataErrors.add(string3);
                Log.error(string3);
            }
        }
        if (n > 0) {
            this.errorMsg = "File contains invalid lines (" + n + ")";
            throw new IndicatorTestException(1, new Exception(string));
        }
        this.timeframe = this.tfRecognizer.getTimeframe();
        Log.info("timeframe is : {} ", (Object)this.timeframe);
        ChartData chartData = new ChartData(this.timeframe, timeDataSeries, dataSeries2, dataSeries3, dataSeries4, dataSeries5, dataSeries6, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null);
        instrumentInfo = new InstrumentInfo();
        instrumentInfo.tickSize = this.tickSize;
        instrumentInfo.tickStep = Math.pow(10.0, -this.digits);
        instrumentInfo.decimals = this.digits;
        chartData.setInstrumentInfo(instrumentInfo);
        return chartData;
    }

    private ChartData loadSourceData(String string, DataSeries dataSeries, boolean bl) throws Exception {
        ArrayList arrayList = SQUtils.loadLines((String)string, (String)";");
        TimeDataSeries timeDataSeries = new TimeDataSeries();
        DataSeries dataSeries2 = new DataSeries();
        DataSeries dataSeries3 = new DataSeries();
        DataSeries dataSeries4 = new DataSeries();
        DataSeries dataSeries5 = new DataSeries();
        DataSeries dataSeries6 = new DataSeries();
        TimeDataSeries timeDataSeries2 = new TimeDataSeries();
        DataSeries dataSeries7 = new DataSeries();
        DataSeries dataSeries8 = new DataSeries();
        DataSeries dataSeries9 = new DataSeries();
        DataSeries dataSeries10 = new DataSeries();
        DataSeries dataSeries11 = new DataSeries();
        TimeDataSeries timeDataSeries3 = new TimeDataSeries();
        DataSeries dataSeries12 = new DataSeries();
        DataSeries dataSeries13 = new DataSeries();
        DataSeries dataSeries14 = new DataSeries();
        DataSeries dataSeries15 = new DataSeries();
        DataSeries dataSeries16 = new DataSeries();
        TimeDataSeries timeDataSeries4 = new TimeDataSeries();
        DataSeries dataSeries17 = new DataSeries();
        DataSeries dataSeries18 = new DataSeries();
        DataSeries dataSeries19 = new DataSeries();
        DataSeries dataSeries20 = new DataSeries();
        DataSeries dataSeries21 = new DataSeries();
        this.tfRecognizer.reset();
        int n = 0;
        boolean bl2 = true;
        long l = 0L;
        long l2 = 0L;
        long l3 = 0L;
        SimpleDateFormat simpleDateFormat = new SimpleDateFormat("yyyy.MM.dd HH:mm:ss");
        double d = 0.0;
        double d2 = 0.0;
        double d3 = 0.0;
        double d4 = 0.0;
        double d5 = 0.0;
        double d6 = 0.0;
        for (int i = 0; i < arrayList.size(); ++i) {
            Object object;
            String string2;
            String[] stringArray = (String[])arrayList.get(i);
            if (stringArray.length < 7) {
                if (++n >= this.maxInvalidLines) continue;
                string2 = "Parse error - Invalid line no." + (i + 1) + ". Expected 7 values, got " + stringArray.length + ".";
                Log.error(string2);
                continue;
            }
            try {
                string2 = stringArray[0];
                object = simpleDateFormat.parse(string2);
                long l4 = ((Date)object).getTime();
                timeDataSeries.add(l4);
                dataSeries2.add(Double.parseDouble(stringArray[1].trim()));
                dataSeries3.add(Double.parseDouble(stringArray[2].trim()));
                dataSeries4.add(Double.parseDouble(stringArray[3].trim()));
                dataSeries5.add(Double.parseDouble(stringArray[4].trim()));
                dataSeries6.add(Double.parseDouble(stringArray[5].trim()));
                dataSeries.add(Double.parseDouble(stringArray[6].trim()));
                this.tfRecognizer.processTime(l4);
                timeDataSeries2.add(l4);
                dataSeries7.add(Double.parseDouble(stringArray[1].trim()));
                dataSeries8.add(Double.parseDouble(stringArray[2].trim()));
                dataSeries9.add(Double.parseDouble(stringArray[3].trim()));
                dataSeries10.add(Double.parseDouble(stringArray[4].trim()));
                timeDataSeries3.add(l4);
                dataSeries12.add(Double.parseDouble(stringArray[1].trim()));
                dataSeries13.add(Double.parseDouble(stringArray[2].trim()));
                dataSeries14.add(Double.parseDouble(stringArray[3].trim()));
                dataSeries15.add(Double.parseDouble(stringArray[4].trim()));
                timeDataSeries4.add(l4);
                dataSeries17.add(Double.parseDouble(stringArray[1].trim()));
                dataSeries18.add(Double.parseDouble(stringArray[2].trim()));
                dataSeries19.add(Double.parseDouble(stringArray[3].trim()));
                dataSeries20.add(Double.parseDouble(stringArray[4].trim()));
                if (bl2) {
                    bl2 = false;
                    l = l4;
                    l2 = l4;
                    l3 = l4;
                    d = Double.parseDouble(stringArray[2].trim());
                    d2 = Double.parseDouble(stringArray[3].trim());
                    d3 = Double.parseDouble(stringArray[2].trim());
                    d4 = Double.parseDouble(stringArray[3].trim());
                    d5 = Double.parseDouble(stringArray[2].trim());
                    d6 = Double.parseDouble(stringArray[3].trim());
                    continue;
                }
                if (!SQTime.isSameDay((long)l, (long)l4)) {
                    l = l4;
                    d = Double.parseDouble(stringArray[2].trim());
                    d2 = Double.parseDouble(stringArray[3].trim());
                } else if (SQTime.isSameDay((long)l, (long)l4)) {
                    dataSeries7.set(0, dataSeries7.get(1));
                    if (Double.parseDouble(stringArray[2].trim()) > d) {
                        dataSeries8.set(0, Double.parseDouble(stringArray[2].trim()));
                        d = Double.parseDouble(stringArray[2].trim());
                    } else {
                        dataSeries8.set(0, dataSeries8.get(1));
                    }
                    if (Double.parseDouble(stringArray[3].trim()) < d2) {
                        dataSeries9.set(0, Double.parseDouble(stringArray[3].trim()));
                        d2 = Double.parseDouble(stringArray[3].trim());
                    } else {
                        dataSeries9.set(0, dataSeries9.get(1));
                    }
                    dataSeries10.set(0, Double.parseDouble(stringArray[4].trim()));
                }
                if (SQTime.isSameWeek((long)l2, (long)l4) == 1) {
                    l2 = l4;
                    d3 = Double.parseDouble(stringArray[2].trim());
                    d4 = Double.parseDouble(stringArray[3].trim());
                } else if (SQTime.isSameWeek((long)l2, (long)l4) == 2) {
                    dataSeries12.set(0, dataSeries12.get(1));
                    if (Double.parseDouble(stringArray[2].trim()) > d3) {
                        dataSeries13.set(0, Double.parseDouble(stringArray[2].trim()));
                        d3 = Double.parseDouble(stringArray[2].trim());
                    } else {
                        dataSeries13.set(0, dataSeries13.get(1));
                    }
                    if (Double.parseDouble(stringArray[3].trim()) < d4) {
                        dataSeries14.set(0, Double.parseDouble(stringArray[3].trim()));
                        d4 = Double.parseDouble(stringArray[3].trim());
                    } else {
                        dataSeries14.set(0, dataSeries14.get(1));
                    }
                    dataSeries15.set(0, Double.parseDouble(stringArray[4].trim()));
                }
                if (!SQTime.isSameMonth((long)l3, (long)l4)) {
                    l3 = l4;
                    d5 = Double.parseDouble(stringArray[2].trim());
                    d6 = Double.parseDouble(stringArray[3].trim());
                    continue;
                }
                if (!SQTime.isSameMonth((long)l3, (long)l4)) continue;
                dataSeries17.set(0, dataSeries17.get(1));
                if (Double.parseDouble(stringArray[2].trim()) > d5) {
                    dataSeries18.set(0, Double.parseDouble(stringArray[2].trim()));
                    d5 = Double.parseDouble(stringArray[2].trim());
                } else {
                    dataSeries18.set(0, dataSeries18.get(1));
                }
                if (Double.parseDouble(stringArray[3].trim()) < d6) {
                    dataSeries19.set(0, Double.parseDouble(stringArray[3].trim()));
                    d6 = Double.parseDouble(stringArray[3].trim());
                } else {
                    dataSeries19.set(0, dataSeries19.get(1));
                }
                dataSeries20.set(0, Double.parseDouble(stringArray[4].trim()));
                continue;
            }
            catch (Exception exception) {
                if (++n >= this.maxInvalidLines) continue;
                object = "Parse error - Invalid line no." + (i + 1) + ". " + exception.getMessage();
                Log.error((String)object);
            }
        }
        bl2 = true;
        double d7 = 0.0;
        double d8 = 0.0;
        double d9 = 0.0;
        double d10 = 0.0;
        double d11 = 0.0;
        double d12 = 0.0;
        double d13 = 0.0;
        double d14 = 0.0;
        double d15 = 0.0;
        for (int i = 0; i < dataSeries7.size(); ++i) {
            if (bl2) {
                bl2 = false;
                l = timeDataSeries2.get(i);
                l2 = timeDataSeries3.get(i);
                l3 = timeDataSeries4.get(i);
                d7 = dataSeries10.get(i);
                d8 = dataSeries15.get(i);
                d9 = dataSeries20.get(i);
                d10 = dataSeries8.get(i);
                d11 = dataSeries13.get(i);
                d12 = dataSeries18.get(i);
                d13 = dataSeries9.get(i);
                d14 = dataSeries14.get(i);
                d15 = dataSeries19.get(i);
                continue;
            }
            if (!SQTime.isSameDay((long)l, (long)timeDataSeries2.get(i))) {
                l = timeDataSeries2.get(i);
                d7 = dataSeries10.get(i);
                d10 = dataSeries8.get(i);
                d13 = dataSeries9.get(i);
            } else if (SQTime.isSameDay((long)l, (long)timeDataSeries2.get(i))) {
                if (bl) {
                    dataSeries10.set(i, d7);
                }
                if (bl) {
                    dataSeries8.set(i, d10);
                }
                if (bl) {
                    dataSeries9.set(i, d13);
                }
            }
            if (SQTime.isSameWeek((long)l2, (long)timeDataSeries3.get(i)) == 1) {
                l2 = timeDataSeries3.get(i);
                d8 = dataSeries15.get(i);
                d11 = dataSeries13.get(i);
                d14 = dataSeries14.get(i);
            } else if (SQTime.isSameWeek((long)l2, (long)timeDataSeries3.get(i)) == 2) {
                if (bl) {
                    dataSeries15.set(i, d8);
                }
                if (bl) {
                    dataSeries13.set(i, d11);
                }
                if (bl) {
                    dataSeries14.set(i, d14);
                }
            }
            if (!SQTime.isSameMonth((long)l3, (long)timeDataSeries4.get(i))) {
                l3 = timeDataSeries4.get(i);
                d9 = dataSeries20.get(i);
                d12 = dataSeries18.get(i);
                d15 = dataSeries19.get(i);
                continue;
            }
            if (!SQTime.isSameMonth((long)l3, (long)timeDataSeries4.get(i))) continue;
            if (bl) {
                dataSeries20.set(i, d9);
            }
            if (bl) {
                dataSeries18.set(i, d12);
            }
            if (!bl) continue;
            dataSeries19.set(i, d15);
        }
        if (n > 0) {
            throw new IndicatorTestException(1, new Exception(string));
        }
        this.timeframe = this.tfRecognizer.getTimeframe();
        Log.info("timeframe is : {} ", (Object)this.timeframe);
        ChartData chartData = new ChartData(this.timeframe, timeDataSeries, dataSeries2, dataSeries3, dataSeries4, dataSeries5, dataSeries6, timeDataSeries2, dataSeries7, dataSeries8, dataSeries9, dataSeries10, timeDataSeries3, dataSeries12, dataSeries13, dataSeries14, dataSeries15, timeDataSeries4, dataSeries17, dataSeries18, dataSeries19, dataSeries20);
        InstrumentInfo instrumentInfo = new InstrumentInfo();
        instrumentInfo.tickSize = this.tickSize;
        instrumentInfo.tickStep = this.tickStep;
        instrumentInfo.decimals = this.digits;
        chartData.setInstrumentInfo(instrumentInfo);
        return chartData;
    }

    private Object getSourceData(ChartData chartData, int n) throws Exception {
        switch (n) {
            case 0: {
                return chartData;
            }
            case 1: {
                return chartData.Open;
            }
            case 2: {
                return chartData.High;
            }
            case 3: {
                return chartData.Low;
            }
            case 4: {
                return chartData.Close;
            }
            case 5: {
                return chartData.Volume;
            }
            case 6: {
                return chartData.Typical;
            }
            case 7: {
                return chartData.Median;
            }
            case 8: {
                return chartData.Weighted;
            }
        }
        throw new Exception("Invalid input data source '" + n + "'");
    }

    public void setstartCompareIndex(int n) throws Exception {
        this.startCompareIndex = n;
    }

    public void setmaxInvalidLines(int n) throws Exception {
        this.maxInvalidLines = n;
    }

    public void setTimeFrame(String string) throws Exception {
        this.timeframe = string;
    }

    public void setdigits(int n) throws Exception {
        this.digits = n;
    }

    public void settickSize(double d) throws Exception {
        this.tickSize = d;
    }

    private Object callMethod(Object object, String string, Object[] objectArray) throws Exception {
        Method method = IndicatorTester.getMethod(object, string, objectArray);
        return method.invoke(object, objectArray);
    }

    public static Method getMethod(Object object, String string, Object[] objectArray) throws Exception {
        Class<?> clazz = object.getClass();
        Class[] classArray = new Class[objectArray.length];
        for (int i = 0; i < objectArray.length; ++i) {
            classArray[i] = IndicatorTester.getParamClass(objectArray[i]);
        }
        return clazz.getMethod(string, classArray);
    }

    private static Class<?> getParamClass(Object object) {
        Class<?> clazz = object.getClass();
        if (clazz.getSimpleName().equals(Integer.class.getSimpleName())) {
            return Integer.TYPE;
        }
        if (clazz.getSimpleName().equals(Double.class.getSimpleName())) {
            return Double.TYPE;
        }
        if (clazz.getSimpleName().equals(Boolean.class.getSimpleName())) {
            return Boolean.TYPE;
        }
        if (clazz.getSimpleName().equals(TypicalDataSeries.class.getSimpleName()) || clazz.getSimpleName().equals(MedianDataSeries.class.getSimpleName()) || clazz.getSimpleName().equals(WeightedDataSeries.class.getSimpleName())) {
            return DataSeries.class;
        }
        return clazz;
    }

    public String getEngine() {
        return this.engine;
    }

    public String getErrorMsg() {
        this.lock.lock();
        try {
            String string = this.errorMsg;
            return string;
        }
        finally {
            this.lock.unlock();
        }
    }

    public void setStartCompareIndex(int n) {
        this.lock.lock();
        try {
            this.startCompareIndex = n;
        }
        finally {
            this.lock.unlock();
        }
    }

    public void setTimeframe(String string) {
        this.lock.lock();
        try {
            this.timeframe = string;
        }
        finally {
            this.lock.unlock();
        }
    }

    public void setMaxInvalidLines(int n) {
        this.lock.lock();
        try {
            this.maxInvalidLines = n;
        }
        finally {
            this.lock.unlock();
        }
    }

    public ArrayList<String> getDataErrors() {
        this.lock.lock();
        try {
            ArrayList<String> arrayList = this.dataErrors;
            return arrayList;
        }
        finally {
            this.lock.unlock();
        }
    }

    public boolean shouldShowGrid() {
        this.lock.lock();
        try {
            boolean bl = this.showGrid;
            return bl;
        }
        finally {
            this.lock.unlock();
        }
    }

    public void reset() {
        this.lock.lock();
        try {
            this.showGrid = false;
            this.dataErrors.clear();
        }
        finally {
            this.lock.unlock();
        }
    }
}

