/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataSeries
 *  com.strategyquant.lib.SQUtils
 */
package com.strategyquant.indicatorTester;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.indicatorTester.IndicatorInfo;
import com.strategyquant.indicatorTester.IndicatorTester;
import com.strategyquant.indicatorTester.IndicatorsLoader;
import com.strategyquant.indicatorTester.IndyParameter;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.ChartData;

public class IndicatorParameters {
    private IndicatorTester tester;
    private int dataSource;

    public IndicatorParameters(IndicatorTester indicatorTester) {
        this.tester = indicatorTester;
    }

    public Object[] convertParams(String string, String[] stringArray) throws Exception {
        IndicatorInfo indicatorInfo = IndicatorsLoader.getIndyByName(string);
        if (indicatorInfo == null) {
            throw new Exception("Indicator '" + string + "' doesn't exist.");
        }
        if (stringArray == null) {
            this.dataSource = 0;
            return null;
        }
        Object[] objectArray = new Object[this.containsDataSeries(indicatorInfo) ? stringArray.length - 1 : stringArray.length];
        int n = 0;
        int n2 = 0;
        for (int i = 0; i < indicatorInfo.parameters.size(); ++i) {
            IndyParameter indyParameter = indicatorInfo.parameters.get(i);
            try {
                if (indyParameter.className.equals(ChartData.class.getSimpleName())) {
                    this.dataSource = 0;
                    continue;
                }
                if (indyParameter.className.equals(DataSeries.class.getSimpleName())) {
                    this.dataSource = this.getDataSource(stringArray[n]);
                } else {
                    objectArray[n2] = this.convertParam(stringArray[n], indyParameter.className);
                    ++n2;
                }
                ++n;
                continue;
            }
            catch (Exception exception) {
                String string2 = "Error while converting parameter '" + indyParameter.name + "': \n" + SQUtils.stackTraceToString((Throwable)exception);
                this.tester.getDataErrors().add(string2);
                throw exception;
            }
        }
        return objectArray;
    }

    public int getDataSource() {
        return this.dataSource;
    }

    private Object convertParam(String string, String string2) {
        if (string2.equals(Integer.class.getSimpleName()) || string2.equals(Integer.TYPE.getSimpleName())) {
            return Integer.parseInt(string);
        }
        if (string2.equals(Double.class.getSimpleName()) || string2.equals(Double.TYPE.getSimpleName())) {
            return Double.parseDouble(string);
        }
        if (string2.equals(Boolean.class.getSimpleName()) || string2.equals(Boolean.TYPE.getSimpleName())) {
            return Boolean.parseBoolean(string);
        }
        return string;
    }

    private boolean containsDataSeries(IndicatorInfo indicatorInfo) {
        for (IndyParameter indyParameter : indicatorInfo.parameters) {
            if (!indyParameter.className.equals(DataSeries.class.getSimpleName())) continue;
            return true;
        }
        return false;
    }

    private int getDataSource(String string) throws Exception {
        switch (string) {
            case "Open": {
                return 1;
            }
            case "High": {
                return 2;
            }
            case "Low": {
                return 3;
            }
            case "Close": {
                return 4;
            }
            case "Volume": {
                return 5;
            }
            case "Typical": {
                return 6;
            }
            case "Median": {
                return 7;
            }
            case "Weighted": {
                return 8;
            }
        }
        throw new Exception("Unknown input price '" + string + "'");
    }
}

