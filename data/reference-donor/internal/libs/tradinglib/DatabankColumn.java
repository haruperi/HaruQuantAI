/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.CustomCellFormat;
import com.strategyquant.tradinglib.IFitnessValue;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.StatsTypeCombination;
import com.strategyquant.tradinglib.table.TableColumn;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DatabankColumn
extends TableColumn
implements IFitnessValue {
    protected static final Logger Log = LoggerFactory.getLogger(DatabankColumn.class);
    public byte valueType = (byte)-1;
    private double target;
    private double avgMin;
    private double avgMax;
    private String[] dependsOn = null;
    private byte[] plTypeRestrictions;
    private byte[] directionRestrictions;
    private String className = null;
    private boolean dependentOnTradingPeriod = false;

    public DatabankColumn(String string, String string2, byte by, double d, double d2, double d3) {
        super(string, string2);
        this.valueType = by;
        this.statsValueName = this.getClass().getSimpleName();
        this.target = d;
        this.avgMin = d2;
        this.avgMax = d3;
    }

    public double getTarget() {
        return this.target;
    }

    public String getValue(ResultsGroup resultsGroup, String string, byte by, byte by2, byte by3) throws Exception {
        SQStats sQStats = this.getStats(resultsGroup, string, by, by2, by3);
        if (sQStats == null) {
            // empty if block
        }
        return this.printValue(sQStats);
    }

    public String exportValue(ResultsGroup resultsGroup, String string, byte by, byte by2, byte by3) throws Exception {
        return this.getValue(resultsGroup, string, by, by2, by3);
    }

    public CustomCellFormat getCustomFormat(byte by, byte by2, byte by3, String string, ResultsGroup resultsGroup) {
        return this.customCellFormat;
    }

    public double getNumericValue(ResultsGroup resultsGroup, String string, byte by, byte by2, byte by3) throws Exception {
        SQStats sQStats = this.getStats(resultsGroup, string, by, by2, by3);
        if (sQStats == null) {
            return 0.0;
        }
        return this.getNumericValue(sQStats);
    }

    public SQStats getStats(ResultsGroup resultsGroup, String string, byte by, byte by2, byte by3) throws Exception {
        if (this.statsValueName == null) {
            throw new Exception(L.t((String)"There is no StatsValue defined for databank column: '%s'!\nYou have to define it or override getValue() method!", (Object[])new Object[]{this.getClass().getSimpleName()}));
        }
        return resultsGroup.subResult(string).statsOrNull(by, by2, by3);
    }

    public boolean setValue(Object object, Object object2) throws Exception {
        if (!this.isEditable()) {
            throw new Exception(L.t((String)"Column '%s' is not editable, you cannot call setValue()!", (Object[])new Object[]{this.getClass().getSimpleName()}));
        }
        throw new Exception(L.t((String)"Column '%s' is editable, it has to implement setValue() method!", (Object[])new Object[]{this.getClass().getSimpleName()}));
    }

    public byte getValueType() {
        return this.valueType;
    }

    public double transformToFitnessRange(double d, double d2, byte by) {
        if (by == 0) {
            by = this.getValueType();
        }
        return this.transformToFitnessRange(d, d2, this.avgMin, this.avgMax, by);
    }

    public double compute(SQStats sQStats, StatsTypeCombination statsTypeCombination, OrdersList ordersList, SettingsMap settingsMap, SQStats sQStats2, SQStats sQStats3, Result result, SettingsMap settingsMap2) throws Exception {
        return this.compute(sQStats, statsTypeCombination, ordersList, settingsMap, sQStats2, sQStats3, result);
    }

    public double compute(SQStats sQStats, StatsTypeCombination statsTypeCombination, OrdersList ordersList, SettingsMap settingsMap, SQStats sQStats2, SQStats sQStats3, Result result) throws Exception {
        return this.compute(sQStats, statsTypeCombination, ordersList, settingsMap, sQStats2, sQStats3);
    }

    public double compute(SQStats sQStats, StatsTypeCombination statsTypeCombination, OrdersList ordersList, SettingsMap settingsMap, SQStats sQStats2, SQStats sQStats3) throws Exception {
        return 0.0;
    }

    protected void setDependencies(String ... stringArray) {
        this.dependsOn = stringArray;
    }

    public String[] getDependencies() {
        return this.dependsOn;
    }

    protected void setPLTypeRestrictions(byte ... byArray) {
        this.plTypeRestrictions = byArray;
    }

    public byte[] getPLTypeRestrictions() {
        return this.plTypeRestrictions;
    }

    protected void setDirectionRestrictions(byte ... byArray) {
        this.directionRestrictions = byArray;
    }

    public byte[] getDirectionRestrictions() {
        return this.directionRestrictions;
    }

    protected double getPLByStatsType(Order order, StatsTypeCombination statsTypeCombination) {
        if (statsTypeCombination.getPLType() == 10) {
            return order.PL;
        }
        if (statsTypeCombination.getPLType() == 20) {
            return order.PctPL_TWR;
        }
        if (statsTypeCombination.getPLType() == 30) {
            return order.PipsPL;
        }
        return 0.0;
    }

    public String getClassName() {
        if (this.className == null) {
            this.className = this.getClass().getSimpleName();
        }
        return this.className;
    }

    public String printHtmlFormatedValue(SQStats sQStats) throws Exception {
        double d = this.getNumericValue(sQStats);
        CustomCellFormat customCellFormat = this.getCustomFormat((byte)0, (byte)10, (byte)127, Double.toString(d), null);
        return customCellFormat.getHtmlContent(d);
    }

    public double convertToDoubleSafe(String string) {
        double d = 0.0;
        try {
            d = Double.parseDouble(SQUtils.extractNumber((String)string));
        }
        catch (Exception exception) {
            // empty catch block
        }
        return d;
    }

    public boolean isDependentOnTradingPeriod() {
        return this.dependentOnTradingPeriod;
    }

    public void setDependentOnTradingPeriod(boolean bl) {
        this.dependentOnTradingPeriod = bl;
    }

    public String getCrossCheckComputedValue(ResultsGroup resultsGroup, double d) throws Exception {
        return null;
    }

    public static enum Color {
        RED,
        GREEN,
        BLUE;

    }
}

