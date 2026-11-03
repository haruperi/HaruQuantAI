/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.table;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.CustomCellFormat;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.debug.Debugger;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class TableColumn
extends Debugger {
    public static final Logger Log = LoggerFactory.getLogger(TableColumn.class);
    public static final int LEFT = 2;
    public static final int RIGHT = 4;
    public static final int CENTER = 0;
    public static final int HORIZONTAL_ALIGNMENT_LEFT = 2;
    public static final int HORIZONTAL_ALIGNMENT_RIGHT = 4;
    public static final int HORIZONTAL_ALIGNMENT_CENTER = 0;
    public static final String Decimal2 = "Decimal2";
    public static final String Decimal4 = "Decimal4";
    public static final String Decimal5 = "Decimal5";
    public static final String Text = "Text";
    public static final String Decimal2Pct = "Decimal2Pct";
    public static final String Decimal2PL = "Decimal2PL";
    public static final String Decimal2Pips = "Decimal2Pips";
    public static final String Integer = "Integer";
    public static final String Time = "Time";
    public static final String currencySymbol = "$";
    public static final String NOT_AVAILABLE = "N/A";
    private String formatType = "Decimal2";
    private int width;
    private String tooltip;
    private String name;
    private boolean editable;
    private boolean fontBold = false;
    private int horizontalAlignment = 2;
    protected CustomCellFormat customCellFormat = new CustomCellFormat();
    protected String statsValueName = null;
    private boolean specialValue = false;

    public TableColumn(String string, String string2) {
        this(string, string2, false);
    }

    public TableColumn(String string, String string2, boolean bl) {
        this.name = string;
        this.formatType = string2;
        this.width = 80;
        this.editable = false;
        this.tooltip = null;
        this.fontBold = bl;
    }

    public boolean isFontBold() {
        return this.fontBold;
    }

    public String getType() {
        return this.formatType;
    }

    public int getWidth() {
        return this.width;
    }

    public void setWidth(int n) {
        this.width = n;
    }

    public void setTooltip(String string) {
        this.tooltip = string;
    }

    public String getTooltip() {
        return this.tooltip;
    }

    public void setName(String string) {
        this.name = string;
    }

    public String getName() {
        return this.name;
    }

    public String getStatsValueName() {
        return this.statsValueName;
    }

    public void setEditable(boolean bl) {
        this.editable = bl;
    }

    public boolean isEditable() {
        return this.editable;
    }

    protected double round2(double d) {
        return SQUtils.round2((double)d);
    }

    protected double round4(double d) {
        return SQUtils.round((double)d, (int)4);
    }

    protected double safeDivide(double d, double d2) {
        return SQUtils.safeDivide((double)d, (double)d2);
    }

    public void printsSpecialValue(boolean bl) {
        this.specialValue = bl;
    }

    public boolean isSpecialValue() {
        return this.specialValue;
    }

    public double getNumericValue(SQStats sQStats) throws Exception {
        try {
            switch (this.formatType) {
                case "Decimal2": 
                case "Decimal4": 
                case "Decimal5": 
                case "Decimal2PL": 
                case "Decimal2Pips": 
                case "Decimal2Pct": 
                case "Time": 
                case "Integer": {
                    return sQStats.getDouble(this.statsValueName, 0.0);
                }
                case "Text": {
                    return 0.0;
                }
            }
            Log.error("Unknown type: '" + this.formatType + "'");
            throw new Exception("Unknown type: " + this.formatType);
        }
        catch (Exception exception) {
            Log.debug("Error while obtaining stats value '" + this.statsValueName + "'. Exc.", (Throwable)exception);
            return 0.0;
        }
    }

    public String printValue(SQStats sQStats) throws Exception {
        double d = 0.0;
        try {
            if (sQStats == null) {
                return NOT_AVAILABLE;
            }
            d = sQStats.getDouble(this.statsValueName, 0.0);
        }
        catch (Exception exception) {
            Log.warn("Cannot parse double value", (Throwable)exception);
            return NOT_AVAILABLE;
        }
        try {
            switch (this.formatType) {
                case "Decimal4": {
                    return Double.toString(SQUtils.round((double)d, (int)4));
                }
                case "Decimal5": {
                    return Double.toString(SQUtils.round((double)d, (int)5));
                }
                case "Decimal2": 
                case "Decimal2PL": 
                case "Decimal2Pips": 
                case "Decimal2Pct": {
                    return Double.toString(SQUtils.round((double)d, (int)2));
                }
                case "Time": {
                    return Long.toString((long)d);
                }
                case "Integer": {
                    return java.lang.Integer.toString((int)d);
                }
                case "Text": {
                    return NOT_AVAILABLE;
                }
            }
        }
        catch (ClassCastException classCastException) {
            Log.debug("Error while obtaining stats value '" + this.statsValueName + "'. Exc.", (Throwable)classCastException);
        }
        return NOT_AVAILABLE;
    }

    public String printPlValue(double d, byte by) throws Exception {
        switch (this.formatType) {
            case "Decimal2": {
                return Double.toString(SQUtils.round((double)d, (int)2));
            }
            case "Decimal4": {
                return Double.toString(SQUtils.round((double)d, (int)4));
            }
            case "Decimal5": {
                return Double.toString(SQUtils.round((double)d, (int)5));
            }
            case "Decimal2PL": {
                return PlTypes.printPL(d, by);
            }
            case "Decimal2Pips": {
                return SQUtils.round((double)d, (int)2) + " pips";
            }
            case "Decimal2Pct": {
                return SQUtils.round((double)d, (int)2) + " %";
            }
            case "Integer": {
                return (int)d + "";
            }
            case "Time": {
                return (long)d + "";
            }
        }
        return d + "";
    }

    public String printPlValue(SQStats sQStats, byte by) throws Exception {
        double d = this.getNumericValue(sQStats);
        return this.printPlValue(d, by);
    }
}

