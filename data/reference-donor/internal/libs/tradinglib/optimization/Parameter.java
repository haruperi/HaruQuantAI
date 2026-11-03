/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.SQTime;
import com.strategyquant.tradinglib.optimization.OptimizationException;

public class Parameter {
    String name;
    byte type;
    double start;
    double stop;
    double step;
    double original;
    private int combinationsCount = -1;
    boolean use;

    Parameter(String string, byte by, boolean bl, double d, double d2, double d3, double d4) {
        this.name = string;
        this.type = by;
        this.use = bl;
        this.start = d;
        this.stop = d2;
        this.step = d3;
        this.original = d4;
        this.combinationsCount = this._getCombinationsCount();
    }

    public static byte getType(String string) {
        switch (string) {
            case "boolean": {
                return 2;
            }
            case "int": {
                return 1;
            }
            case "double": {
                return 4;
            }
            case "time": {
                return 5;
            }
        }
        return 0;
    }

    public byte getType() {
        return this.type;
    }

    public String getName() {
        return this.name;
    }

    public int getCombinationsCount() {
        return this.combinationsCount;
    }

    private int _getCombinationsCount() {
        if (!this.use) {
            return 1;
        }
        if (this.type == 2) {
            return 2;
        }
        if (this.type == 5) {
            int n = SQTime.HHMMToMinutes((int)((int)this.start));
            int n2 = SQTime.HHMMToMinutes((int)((int)this.stop));
            int n3 = SQTime.HHMMToMinutes((int)((int)this.step));
            if (n3 == 0 || n2 == n) {
                return 1;
            }
            return Math.abs((n2 - n) / n3 + 1);
        }
        if (this.step == 0.0 || this.stop == this.start) {
            return 1;
        }
        return (int)Math.abs((double)Math.round((this.stop - this.start) / this.step) + 1.0);
    }

    public double getOriginalValue() {
        return this.original;
    }

    public double getStart() {
        return this.start;
    }

    public double getStop() {
        return this.stop;
    }

    public double getStep() {
        return this.step;
    }

    public boolean isUsed() {
        return this.use;
    }

    public double getValueByIndex(int n) throws OptimizationException {
        double d;
        if (n < 0) {
            return this.original;
        }
        if (n > this.combinationsCount - 1) {
            throw new OptimizationException(String.format("Index out of range. Parameter: '%s', index: %d", this.name, n));
        }
        if (this.type == 2) {
            if (n <= 0) {
                return this.start > 0.0 ? 1 : 0;
            }
            return !(this.start > 0.0) ? 1 : 0;
        }
        if (this.type == 5) {
            int n2;
            int n3 = SQTime.HHMMToMinutes((int)((int)this.start));
            int n4 = SQTime.HHMMToMinutes((int)((int)this.step));
            int n5 = n2 = n < 0 ? (int)this.original : n3 + n * n4;
            n2 = n2 < 0 ? 0 : (n2 > 1439 ? 1439 : n2);
            return SQTime.minutesToHHMM((int)n2);
        }
        double d2 = this.start;
        double d3 = this.step;
        double d4 = d = n < 0 ? this.original : d2 + (double)n * d3;
        if (this.type == 1) {
            return (int)d;
        }
        return d;
    }

    public Parameter clone() {
        return new Parameter(this.name, this.type, this.use, this.start, this.stop, this.step, this.original);
    }
}

