/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.databank;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.ResultTypes;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SampleTypes;
import com.strategyquant.tradinglib.StatsDontExistException;
import com.strategyquant.tradinglib.crosscheck.CrossCheckConditionValue;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DatabankTableColumnEntry
implements IXMLAble {
    public static final Logger Log = LoggerFactory.getLogger((String)"TableColumnEntry");
    public DatabankColumn tableColumn;
    public String resultType = "main";
    public byte direction = 0;
    public byte sampleType = (byte)127;
    public byte plType = (byte)10;
    public int confidenceLevel = 50;
    public int market = 1;
    public byte subresult = (byte)30;
    public boolean showMainResult = true;
    public Element elValue = null;

    public DatabankTableColumnEntry() {
    }

    public DatabankTableColumnEntry(DatabankColumn databankColumn, String string, byte by, byte by2, byte by3) {
        this(databankColumn, string, by, by2, by3, 50, 1, 30, true);
    }

    public DatabankTableColumnEntry(DatabankColumn databankColumn, String string, byte by, byte by2, byte by3, int n, int n2, byte by4, boolean bl) {
        this.tableColumn = databankColumn;
        this.resultType = string;
        this.direction = by;
        this.sampleType = by3;
        this.plType = by2;
        this.confidenceLevel = n;
        this.market = n2;
        this.subresult = by4;
        this.showMainResult = bl;
    }

    public String getColumnEntryName() {
        ICrossCheck iCrossCheck = ResultTypes.findCrossCheckByType(this.resultType);
        if (iCrossCheck != null) {
            return iCrossCheck.getColumnTitle(this.tableColumn.getName(), this.elValue, new Object[0]);
        }
        String string = this.getResultType(this.resultType);
        String string2 = string.isEmpty() ? "" : string + ", ";
        String string3 = this.direction == 0 ? "" : this.getDirection(this.direction);
        String string4 = string3.isEmpty() ? "" : string3 + ", ";
        String string5 = this.sampleType == 0 ? "" : this.getSampleType(this.sampleType);
        String string6 = string5.isEmpty() ? "" : string5 + ", ";
        String string7 = this.plType == 0 ? "" : this.getPlType(this.plType);
        String string8 = string7.isEmpty() ? "" : string7 + ", ";
        String string9 = "";
        string9 = string2 + string4 + string6 + string8;
        if (!string9.equals("")) {
            string9 = string9.trim();
            string9 = SQUtils.replaceLast((String)string9, (String)",", (String)"");
            string9 = " (" + string9 + ")";
        }
        return this.tableColumn.getName() + string9;
    }

    private String getResultType(String string) {
        return string.equals("main") ? "" : ResultTypes.typeToString(string);
    }

    private String getDirection(byte by) {
        switch (by) {
            case 0: {
                return "";
            }
            case 1: {
                return "Long";
            }
            case -1: {
                return "Short";
            }
        }
        return "?";
    }

    private String getSampleType(byte by) {
        if (by == 127) {
            return "";
        }
        return SampleTypes.typeToString(by);
    }

    private String getPlType(byte by) {
        switch (by) {
            case 10: {
                return "";
            }
            case 20: {
                return "%";
            }
            case 30: {
                return "Pips";
            }
        }
        return "?";
    }

    public String getValue(Object object) {
        return this.getValue(object, false);
    }

    public String exportValue(Object object) {
        return this.getValue(object, true);
    }

    private String getValue(Object object, boolean bl) {
        block12: {
            try {
                ResultsGroup resultsGroup = (ResultsGroup)object;
                if (ResultTypes.isCrossCheck(this.resultType)) {
                    String string = this.tryToReturnWFTextValue(resultsGroup, bl);
                    if (string != null) {
                        return string;
                    }
                    CrossCheckConditionValue crossCheckConditionValue = new CrossCheckConditionValue(this.tableColumn.getClassName(), this.resultType, 0, this.elValue);
                    if (crossCheckConditionValue.hasValue(resultsGroup)) {
                        if (this.tableColumn.isSpecialValue()) {
                            return crossCheckConditionValue.printValue(resultsGroup);
                        }
                        double d = crossCheckConditionValue.getValue(resultsGroup);
                        String string2 = this.tableColumn.getCrossCheckComputedValue(resultsGroup, d);
                        if (string2 != null) {
                            return string2;
                        }
                        return Double.toString(d);
                    }
                    if (this.showMainResult) {
                        if (bl) {
                            return this.tableColumn.exportValue(resultsGroup, this.getCorrectResultKey(resultsGroup), this.direction, this.plType, this.sampleType);
                        }
                        return this.tableColumn.getValue(resultsGroup, this.getCorrectResultKey(resultsGroup), this.direction, this.plType, this.sampleType);
                    }
                    break block12;
                }
                if (bl) {
                    return this.tableColumn.exportValue(resultsGroup, this.getCorrectResultKey(resultsGroup), this.direction, this.plType, this.sampleType);
                }
                return this.tableColumn.getValue(resultsGroup, this.getCorrectResultKey(resultsGroup), this.direction, this.plType, this.sampleType);
            }
            catch (StatsDontExistException statsDontExistException) {
            }
            catch (CrossCheckDataNotExistException crossCheckDataNotExistException) {
            }
            catch (Exception exception) {
                Log.error("Cannot print value of databank column '" + this.tableColumn.getName() + "'. Exc.", (Throwable)exception);
            }
        }
        return "N/A";
    }

    private String tryToReturnWFTextValue(ResultsGroup resultsGroup, boolean bl) {
        String string = null;
        try {
            if ((this.resultType.equals("WalkForwardMatrix") || this.resultType.equals("WalkForwardOptimization")) && resultsGroup.getBestWFResultKey() != null) {
                if (this.tableColumn.getClassName().equals("Symbol") || this.tableColumn.getClassName().equals("TimeFrame")) {
                    if (bl) {
                        return this.tableColumn.exportValue(resultsGroup, resultsGroup.getMainResultKey(), this.direction, this.plType, this.sampleType);
                    }
                    return this.tableColumn.getValue(resultsGroup, resultsGroup.getMainResultKey(), this.direction, this.plType, this.sampleType);
                }
                if (this.tableColumn.getClassName().equals("MiniEquityChart")) {
                    if (bl) {
                        return this.tableColumn.exportValue(resultsGroup, resultsGroup.getBestWFResultKey(), this.direction, this.plType, this.sampleType);
                    }
                    return this.tableColumn.getValue(resultsGroup, resultsGroup.getBestWFResultKey(), this.direction, this.plType, this.sampleType);
                }
                if (this.tableColumn.getClassName().equals("Fitness")) {
                    if (bl) {
                        return this.tableColumn.exportValue(resultsGroup, resultsGroup.getBestWFResultKey(), this.direction, this.plType, this.sampleType);
                    }
                    return this.tableColumn.getValue(resultsGroup, resultsGroup.getBestWFResultKey(), this.direction, this.plType, this.sampleType);
                }
            }
        }
        catch (Exception exception) {
            Log.error("Errow while trying to return CrossCheck value. Exc.", (Throwable)exception);
        }
        return string;
    }

    public double getNumericValue(ResultsGroup resultsGroup) throws Exception {
        if (ResultTypes.isCrossCheck(this.resultType)) {
            CrossCheckConditionValue crossCheckConditionValue = new CrossCheckConditionValue(this.tableColumn.getClassName(), this.resultType, 0, this.elValue);
            return crossCheckConditionValue.getValue(resultsGroup);
        }
        return this.tableColumn.getNumericValue(resultsGroup, this.getCorrectResultKey(resultsGroup), this.direction, this.plType, this.sampleType);
    }

    private String getCorrectResultKey(ResultsGroup resultsGroup) throws Exception {
        return this.resultType.equals("portfolio") ? "Portfolio" : resultsGroup.getMainResultKey();
    }

    public Element getXML() {
        Element element = new Element("Column");
        element.setAttribute("class", this.tableColumn.getClass().getSimpleName());
        element.setAttribute("name", this.tableColumn.getName());
        element.setAttribute("resultType", String.valueOf(this.resultType));
        element.setAttribute("sampleType", String.valueOf(this.sampleType));
        element.setAttribute("direction", String.valueOf(this.direction));
        element.setAttribute("plType", String.valueOf(this.plType));
        element.setAttribute("confidenceLevel", String.valueOf(this.confidenceLevel));
        element.setAttribute("market", String.valueOf(this.market));
        element.setAttribute("subresult", String.valueOf(this.subresult));
        element.setAttribute("showMainResult", String.valueOf(this.showMainResult));
        return element;
    }

    public void setFromXML(Element element) throws Exception {
        Object object;
        String string = element.getAttributeValue("class");
        if (string == null || string.equals("")) {
            throw new Exception(L.t((String)"Empty column definition.", (Object[])new Object[0]));
        }
        this.tableColumn = (DatabankColumn)DatabankColumns.get().createNew(string);
        if (this.tableColumn == null) {
            throw new Exception(L.t((String)"Invalid databank column '%s'.", (Object[])new Object[]{string}));
        }
        if (element.getAttributeValue("resultType") != null && ResultTypes.isValid((String)(object = element.getAttributeValue("resultType")))) {
            this.resultType = object;
        }
        if (element.getAttributeValue("sampleType") != null) {
            this.sampleType = Byte.parseByte(element.getAttributeValue("sampleType"));
        }
        if (element.getAttributeValue("direction") != null) {
            this.direction = Byte.parseByte(element.getAttributeValue("direction"));
        }
        if (element.getAttributeValue("plType") != null && PlTypes.isValid((Byte)(object = Byte.valueOf(Byte.parseByte(element.getAttributeValue("plType")))))) {
            this.plType = (Byte)object;
        }
        if (element.getAttributeValue("confidenceLevel") != null) {
            this.confidenceLevel = Integer.parseInt(element.getAttributeValue("confidenceLevel"));
        }
        if (element.getAttributeValue("market") != null) {
            this.market = Integer.parseInt(element.getAttributeValue("market"));
        }
        if (element.getAttributeValue("subresult") != null) {
            this.subresult = Byte.parseByte(element.getAttributeValue("subresult"));
        }
        if (element.getAttributeValue("showMainResult") != null) {
            this.showMainResult = Boolean.parseBoolean(element.getAttributeValue("showMainResult"));
        }
        this.elValue = element;
    }
}

