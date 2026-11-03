/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 */
package com.strategyquant.tradinglib.conditions;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.Directions;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.ResultTypes;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SampleTypes;
import com.strategyquant.tradinglib.conditions.IConditionValue;
import java.util.HashMap;

public class ColumnConditionValue
implements IConditionValue {
    private String resultType;
    private byte direction;
    private byte plType;
    private byte sampleType;
    private byte columnType;
    private int pctRatio;
    DatabankColumn column;

    public ColumnConditionValue(DatabankColumn databankColumn, String string, byte by, byte by2, byte by3, int n) {
        this.column = databankColumn;
        this.resultType = string;
        this.direction = by;
        this.plType = by2;
        this.sampleType = by3;
        this.pctRatio = n;
    }

    @Override
    public double getStatsValue(Object ... objectArray) throws Exception {
        ResultsGroup resultsGroup = (ResultsGroup)objectArray[0];
        String string = this.resultType.equals("portfolio") ? "Portfolio" : resultsGroup.getMainResultKey();
        return this.column.getNumericValue(resultsGroup, string, this.direction, this.plType, this.getSampleType(objectArray));
    }

    @Override
    public double getValue(Object ... objectArray) throws Exception {
        double d = this.getStatsValue(objectArray);
        if (this.pctRatio > 0) {
            d *= (double)this.pctRatio / 100.0;
        }
        return d;
    }

    @Override
    public String getLabel(Object ... objectArray) throws Exception {
        double d = this.getStatsValue(objectArray);
        String string = String.format("%s (%s)", this.getColumnName(objectArray), this.column.printPlValue(d, this.plType));
        if (this.pctRatio > 0) {
            string = this.pctRatio + "% of " + string;
        }
        return string;
    }

    public String toString() {
        String string = this.getColumnName(new Object[0]);
        if (this.pctRatio > 0) {
            string = this.pctRatio + "% of " + string;
        }
        return string;
    }

    private String getColumnName(Object ... objectArray) {
        String string = "";
        string = string + ResultTypes.typeToString(this.resultType) + ", ";
        string = string + (this.sampleType == 127 ? "" : SampleTypes.typeToString(this.getSampleType(objectArray)) + ", ");
        string = string + (this.direction == 0 ? "" : Directions.typeToString(this.direction) + ", ");
        string = string + (this.plType == 10 ? "" : PlTypes.typeToString(this.plType) + ", ");
        string = string.trim();
        string = SQUtils.replaceLast((String)string, (String)",", (String)"");
        string = "[" + string + "]";
        return L.t((String)this.column.getName(), (Object[])new Object[0]) + string;
    }

    public IConditionValue getClone() {
        return new ColumnConditionValue(this.column, this.resultType, this.direction, this.plType, this.sampleType, this.pctRatio);
    }

    @Override
    public String getTitle() throws Exception {
        return this.getColumnName(new Object[0]);
    }

    @Override
    public String getCrossCheckSettingName() {
        return null;
    }

    @Override
    public String getConditionParamValue(String string, String string2) {
        if (string.equals("SampleType")) {
            return this.sampleType + "";
        }
        return string2;
    }

    @Override
    public boolean statsExists(Object ... objectArray) {
        try {
            ResultsGroup resultsGroup = (ResultsGroup)objectArray[0];
            String string = this.resultType.equals("portfolio") ? "Portfolio" : resultsGroup.getMainResultKey();
            return this.column.getStats(resultsGroup, string, this.direction, this.plType, this.getSampleType(objectArray)) != null;
        }
        catch (Exception exception) {
            return false;
        }
    }

    private byte getSampleType(Object ... objectArray) {
        HashMap hashMap;
        byte by = this.sampleType;
        if ((this.sampleType == 66 || this.sampleType == 77) && objectArray.length > 1 && objectArray[1] instanceof HashMap && (hashMap = (HashMap)objectArray[1]).containsKey("SampleType")) {
            by = (Byte)hashMap.get("SampleType");
        }
        return by;
    }

    @Override
    public String printFormatedValue(double d) throws Exception {
        return this.column.printPlValue(d, this.plType);
    }
}

