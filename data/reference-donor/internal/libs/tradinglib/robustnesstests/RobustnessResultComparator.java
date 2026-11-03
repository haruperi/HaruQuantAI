/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.robustnesstests;

import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.robustnesstests.RobustnessResults;
import java.util.Comparator;

public class RobustnessResultComparator
implements Comparator<RobustnessResults> {
    private static final int TypeDouble = 1;
    private static final int TypeInt = 2;
    private static final int TypeUncomparable = 3;
    private DatabankColumn column;
    private byte valueType;
    private int columnType;
    private String statsValue;

    public RobustnessResultComparator(DatabankColumn databankColumn) {
        this.column = databankColumn;
        this.valueType = databankColumn.getValueType();
        if (this.valueType == 3) {
            this.valueType = 1;
        }
        this.columnType = this.recognizeColumnType(databankColumn.getType());
        this.statsValue = databankColumn.getStatsValueName();
    }

    private int recognizeColumnType(String string) {
        if (string.contains("Decimal")) {
            return 1;
        }
        if (string.contains("Integer")) {
            return 2;
        }
        return 3;
    }

    @Override
    public int compare(RobustnessResults robustnessResults, RobustnessResults robustnessResults2) {
        double d;
        double d2;
        if (this.columnType == 3) {
            return 0;
        }
        if (this.statsValue == null) {
            return 0;
        }
        if (this.columnType == 2) {
            d2 = robustnessResults.getOriginalStats().getInt(this.statsValue);
            d = robustnessResults2.getOriginalStats().getInt(this.statsValue);
        } else {
            d2 = robustnessResults.getOriginalStats().getDouble(this.statsValue);
            d = robustnessResults2.getOriginalStats().getDouble(this.statsValue);
        }
        if (this.valueType == 2) {
            if (d2 > d) {
                return 1;
            }
            if (d2 < d) {
                return -1;
            }
            return 0;
        }
        if (d2 > d) {
            return -1;
        }
        if (d2 < d) {
            return 1;
        }
        return 0;
    }
}

