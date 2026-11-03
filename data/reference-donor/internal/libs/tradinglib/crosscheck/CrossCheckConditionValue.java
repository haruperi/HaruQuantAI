/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.pluginlib.SQPluginManager
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.crosscheck;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.conditions.IConditionValue;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.optimization.WalkForwardColumns;
import com.strategyquant.tradinglib.table.TableColumn;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CrossCheckConditionValue
implements IConditionValue {
    private static final Logger Log = LoggerFactory.getLogger(CrossCheckConditionValue.class);
    private String columnName;
    private int pctRatio;
    private String crossCheckSettingName;
    private Element elColumn;
    private byte plType;
    private String columnNameText;
    private ICrossCheck crossCheck;
    private TableColumn tableColumn;

    public CrossCheckConditionValue(String string, String string2, int n, Element element) throws Exception {
        block4: {
            this.columnNameText = "NA";
            this.crossCheck = null;
            this.columnName = string;
            this.pctRatio = n;
            this.crossCheckSettingName = string2;
            this.elColumn = element;
            this.plType = XMLUtil.getByteAttr((Element)element, (String)"plType", (byte)10);
            try {
                if (DatabankColumns.get().checkClassExists(string)) {
                    this.tableColumn = (TableColumn)DatabankColumns.get().findClassByName(string);
                    break block4;
                }
                if (WalkForwardColumns.get().checkClassExists(string)) {
                    this.tableColumn = (TableColumn)WalkForwardColumns.get().findClassByName(string);
                    break block4;
                }
                throw new Exception(L.t((String)"Column doesn't exist.", (Object[])new Object[0]));
            }
            catch (Exception exception) {
                Log.error("Cannot find column wit name '{}'", (Object)string);
                throw new Exception(L.t((String)"Cannot find column wit name '%s'", (Object[])new Object[]{string}));
            }
        }
        this.crossCheck = this.findPluginByName();
        this.columnNameText = this.crossCheck.getColumnTitle(this.tableColumn.getName(), element, new Object[0]);
    }

    @Override
    public double getStatsValue(Object ... objectArray) throws Exception {
        ResultsGroup resultsGroup = (ResultsGroup)objectArray[0];
        double d = 0.0;
        try {
            ICrossCheck iCrossCheck = this.findPluginByName();
            d = iCrossCheck.getStatsValue(resultsGroup, this.columnName, this.elColumn, objectArray);
        }
        catch (CrossCheckDataNotExistException crossCheckDataNotExistException) {
            throw crossCheckDataNotExistException;
        }
        catch (Exception exception) {
            Log.error("Error while evaluating CrossCheck acceptance condition.", (Throwable)exception);
        }
        return d;
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
        String string = this.crossCheck.getColumnTitle(this.columnName, this.elColumn, objectArray);
        double d = this.getStatsValue(objectArray);
        String string2 = String.format("%s[" + L.t((String)"Cross Check  data", (Object[])new Object[]{true}) + "] (%s)", string, this.tableColumn.printPlValue(d, this.plType));
        if (this.pctRatio > 0) {
            string2 = this.pctRatio + "% of " + string2;
        }
        return string2;
    }

    public String toString() {
        String string = String.format("%s[" + L.t((String)"Cross Check  data", (Object[])new Object[]{true}) + "]", this.columnNameText);
        if (this.pctRatio > 0) {
            string = this.pctRatio + "% of " + string;
        }
        return string;
    }

    private ICrossCheck findPluginByName() throws Exception {
        for (ICrossCheck iCrossCheck : SQPluginManager.getPlugins(ICrossCheck.class)) {
            if (!iCrossCheck.getSettingName().equals(this.crossCheckSettingName)) continue;
            return iCrossCheck;
        }
        throw new Exception(L.t((String)"CrossCheck method '%' doesn't exist.", (Object[])new Object[]{this.crossCheckSettingName}));
    }

    public IConditionValue getClone() throws Exception {
        return new CrossCheckConditionValue(this.columnName, this.crossCheckSettingName, this.pctRatio, this.elColumn);
    }

    public String printValue(Object ... objectArray) throws Exception {
        ResultsGroup resultsGroup = (ResultsGroup)objectArray[0];
        ICrossCheck iCrossCheck = this.findPluginByName();
        if (this.tableColumn != null && this.tableColumn.isSpecialValue()) {
            return iCrossCheck.printSpecialValue(resultsGroup, this.columnName, this.elColumn, objectArray);
        }
        return Double.toString(iCrossCheck.getStatsValue(resultsGroup, this.columnName, this.elColumn, objectArray));
    }

    @Override
    public String getTitle() throws Exception {
        return this.columnNameText;
    }

    @Override
    public String getCrossCheckSettingName() {
        return this.crossCheckSettingName;
    }

    public boolean hasValue(Object ... objectArray) {
        try {
            ResultsGroup resultsGroup = (ResultsGroup)objectArray[0];
            ICrossCheck iCrossCheck = this.findPluginByName();
            return iCrossCheck.hasStatsValue(resultsGroup, this.columnName, this.elColumn, objectArray);
        }
        catch (Exception exception) {
            Log.error("Error while evaluating CrossCheck acceptance condition.", (Throwable)exception);
            return false;
        }
    }

    @Override
    public String getConditionParamValue(String string, String string2) {
        if (string.equals("AdditionalMarket")) {
            return XMLUtil.getIntAttr((Element)this.elColumn, (String)"market", (int)1) + "";
        }
        if (string.equals("SampleType")) {
            return XMLUtil.getByteAttr((Element)this.elColumn, (String)"sampleType", (byte)127) + "";
        }
        return string2;
    }

    @Override
    public boolean statsExists(Object ... objectArray) {
        try {
            ResultsGroup resultsGroup = (ResultsGroup)objectArray[0];
            ICrossCheck iCrossCheck = this.findPluginByName();
            return iCrossCheck.hasStatsValue(resultsGroup, this.columnName, this.elColumn, objectArray);
        }
        catch (Exception exception) {
            Log.error("Error while evaluating CrossCheck acceptance condition.", (Throwable)exception);
            return false;
        }
    }

    @Override
    public String printFormatedValue(double d) throws Exception {
        return this.tableColumn.printPlValue(d, this.plType);
    }
}

