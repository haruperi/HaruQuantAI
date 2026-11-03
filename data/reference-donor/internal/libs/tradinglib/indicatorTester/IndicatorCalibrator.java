/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.DataSeries
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.IDataLoader
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.dataseries.TimeDataSeries
 *  com.strategyquant.lib.L
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.indicatorTester;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.DataSeries;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.dataseries.TimeDataSeries;
import com.strategyquant.indicatorTester.CalibrationInfo;
import com.strategyquant.indicatorTester.CalibrationRangesInfo;
import com.strategyquant.indicatorTester.IndicatorInfo;
import com.strategyquant.indicatorTester.IndicatorTester;
import com.strategyquant.indicatorTester.IndicatorsLoader;
import com.strategyquant.indicatorTester.IndyParameter;
import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.indicator.IndicatorsObj;
import java.lang.reflect.Method;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class IndicatorCalibrator {
    public static final Logger Log = LoggerFactory.getLogger((String)"IndicatorCalibrator");

    public ArrayList<CalibrationInfo> calibrate(String[] stringArray, String[] stringArray2, int n) throws Exception {
        if (n == 1316847364 || n == -1816889229) {
            throw new Exception(L.t((String)"Indicator calibration is not supported for AlgoCloud Stockpicker / Single-asset engine.", (Object[])new Object[0]));
        }
        ArrayList<CalibrationInfo> arrayList = new ArrayList<CalibrationInfo>();
        ArrayList<ChartData> arrayList2 = new ArrayList<ChartData>();
        for (int i = 0; i < stringArray.length; ++i) {
            arrayList2.add(this.loadChartData(stringArray[i], stringArray2[i]));
        }
        IndicatorsObj indicatorsObj = StrategyBase.createIndicatorsObj(n);
        ArrayList<IndicatorInfo> arrayList3 = IndicatorsLoader.getIndicators();
        ArrayList<Double> arrayList4 = new ArrayList<Double>();
        for (int i = 0; i < arrayList3.size(); ++i) {
            String string;
            IndicatorInfo indicatorInfo = arrayList3.get(i);
            if (indicatorInfo.ignored || !this.checkReturnType(indicatorInfo.returnType) || (string = IndicatorsLoader.correctIndyName(indicatorInfo.simpleName)).equals("DataLoggingIndy")) continue;
            Log.debug("Calibrating indicator " + string + "...");
            try {
                CalibrationInfo calibrationInfo = new CalibrationInfo(string);
                calibrationInfo.name = indicatorInfo.title;
                for (int j = 0; j < arrayList2.size(); ++j) {
                    ChartData chartData = (ChartData)arrayList2.get(j);
                    ArrayList<Object[]> arrayList5 = this.getParametersVariations(indicatorInfo, chartData);
                    CalibrationRangesInfo calibrationRangesInfo = new CalibrationRangesInfo(chartData.Symbol, chartData.Timeframe);
                    calibrationRangesInfo.minValue = 1.0E9;
                    calibrationRangesInfo.maxValue = -1.0E9;
                    Method method = IndicatorTester.getMethod(indicatorsObj, string, arrayList5.get(0));
                    arrayList4.clear();
                    for (int k = 0; k < arrayList5.size(); ++k) {
                        Object object = method.invoke((Object)indicatorsObj, arrayList5.get(k));
                        for (int i2 = 0; i2 < indicatorInfo.outputBuffers.size(); ++i2) {
                            String string2 = indicatorInfo.outputBuffers.get(i2);
                            DataSeries dataSeries = (DataSeries)object.getClass().getField(string2).get(object);
                            dataSeries.setShift(0);
                            for (int i3 = 0; i3 < dataSeries.size(); ++i3) {
                                arrayList4.add(dataSeries.get(i3));
                            }
                        }
                    }
                    double d = this.getMean(arrayList4);
                    double d2 = this.getStdDev(arrayList4, d);
                    calibrationRangesInfo.minValue = d - d2;
                    calibrationRangesInfo.maxValue = d + d2;
                    calibrationRangesInfo.fixValues();
                    calibrationInfo.ranges.add(calibrationRangesInfo);
                }
                arrayList.add(calibrationInfo);
                continue;
            }
            catch (Exception exception) {
                Log.error("Cannot calibrate indicator '" + string + "'", (Throwable)exception);
            }
        }
        return arrayList;
    }

    private double getMean(ArrayList<Double> arrayList) throws TradingException {
        double d = 0.0;
        for (int i = 0; i < arrayList.size(); ++i) {
            d += arrayList.get(i).doubleValue();
        }
        return d / (double)arrayList.size();
    }

    private double getStdDev(ArrayList<Double> arrayList, double d) throws TradingException {
        double d2 = 0.0;
        for (int i = 0; i < arrayList.size(); ++i) {
            d2 += Math.pow(arrayList.get(i) - d, 2.0);
        }
        return Math.sqrt(d2 / (double)arrayList.size());
    }

    private ChartData loadChartData(String string, String string2) throws Exception {
        if (!DataManager.checkDataExists((String)"History", (String)string)) {
            throw new Exception(L.t((String)"Symbol '%s' doesn't exist", (Object[])new Object[]{string}));
        }
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string);
        ChartDef chartDef = new ChartDef("History", string, string2, dataInfo.dateFrom, dataInfo.dateTo, dataInfo.symbolInfo.defaultSpread, "No Session");
        try (IDataLoader iDataLoader = null;){
            iDataLoader = DataManager.getDataLoader((ChartDef)chartDef, (int)1);
            iDataLoader.open();
            TimeDataSeries timeDataSeries = new TimeDataSeries();
            DataSeries dataSeries = new DataSeries();
            DataSeries dataSeries2 = new DataSeries();
            DataSeries dataSeries3 = new DataSeries();
            DataSeries dataSeries4 = new DataSeries();
            DataSeries dataSeries5 = new DataSeries();
            VersatileData versatileData = new VersatileData();
            while (iDataLoader.hasNextTick()) {
                iDataLoader.getNextTick(versatileData);
                timeDataSeries.add(versatileData.time);
                dataSeries.add(versatileData.open);
                dataSeries2.add(versatileData.high);
                dataSeries3.add(versatileData.low);
                dataSeries4.add(versatileData.close);
                dataSeries5.add(versatileData.volume);
            }
            iDataLoader.close();
            ChartData chartData = new ChartData(string2, timeDataSeries, dataSeries, dataSeries2, dataSeries3, dataSeries4, dataSeries5, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null);
            chartData.Symbol = string;
            ChartData chartData2 = chartData;
            return chartData2;
        }
    }

    private ArrayList<Object[]> getParametersVariations(IndicatorInfo indicatorInfo, ChartData chartData) {
        ArrayList<Object[]> arrayList = new ArrayList<Object[]>();
        Object[] objectArray = this.getDefaultParameters(indicatorInfo, chartData);
        for (int i = 0; i < indicatorInfo.parameters.size(); ++i) {
            int n;
            String[] stringArray;
            IndyParameter indyParameter = indicatorInfo.parameters.get(i);
            if (indyParameter.className.equals(Integer.class.getSimpleName()) || indyParameter.className.equals(Integer.TYPE.getSimpleName())) {
                if (indyParameter.calibrationValues == null) continue;
                stringArray = indyParameter.calibrationValues.split(",");
                for (n = 0; n < stringArray.length; ++n) {
                    Object[] objectArray2;
                    int n2 = Integer.parseInt(stringArray[n]);
                    if (arrayList.size() > n) {
                        objectArray2 = arrayList.get(n);
                        objectArray2[i] = n2;
                        continue;
                    }
                    objectArray2 = this.cloneDefaultParameters(objectArray);
                    objectArray2[i] = n2;
                    arrayList.add(objectArray2);
                }
                continue;
            }
            if (!indyParameter.className.equals(Double.class.getSimpleName()) && !indyParameter.className.equals(Double.TYPE.getSimpleName()) || indyParameter.calibrationValues == null) continue;
            stringArray = indyParameter.calibrationValues.split(",");
            for (n = 0; n < stringArray.length; ++n) {
                Object[] objectArray3;
                double d = Double.parseDouble(stringArray[n]);
                if (arrayList.size() > n) {
                    objectArray3 = arrayList.get(n);
                    objectArray3[i] = d;
                    continue;
                }
                objectArray3 = this.cloneDefaultParameters(objectArray);
                objectArray3[i] = d;
                arrayList.add(objectArray3);
            }
        }
        if (arrayList.isEmpty()) {
            arrayList.add(objectArray);
        }
        return arrayList;
    }

    private Object[] getDefaultParameters(IndicatorInfo indicatorInfo, ChartData chartData) {
        Object[] objectArray = new Object[indicatorInfo.parameters.size()];
        for (int i = 0; i < indicatorInfo.parameters.size(); ++i) {
            IndyParameter indyParameter = indicatorInfo.parameters.get(i);
            objectArray[i] = indyParameter.className.equals(ChartData.class.getSimpleName()) ? chartData : (indyParameter.className.equals(DataSeries.class.getSimpleName()) ? chartData.Open : (indyParameter.className.equals(Integer.class.getSimpleName()) || indyParameter.className.equals(Integer.TYPE.getSimpleName()) ? Integer.valueOf(Integer.parseInt(indyParameter.defaultValue)) : (indyParameter.className.equals(Double.class.getSimpleName()) || indyParameter.className.equals(Double.TYPE.getSimpleName()) ? Double.valueOf(Double.parseDouble(indyParameter.defaultValue)) : indyParameter.defaultValue)));
        }
        return objectArray;
    }

    private Object[] cloneDefaultParameters(Object[] objectArray) {
        Object[] objectArray2 = new Object[objectArray.length];
        for (int i = 0; i < objectArray.length; ++i) {
            objectArray2[i] = objectArray[i];
        }
        return objectArray2;
    }

    private boolean checkReturnType(int n) {
        switch (n) {
            case 0: 
            case 1: 
            case 7: {
                return true;
            }
        }
        return false;
    }
}

