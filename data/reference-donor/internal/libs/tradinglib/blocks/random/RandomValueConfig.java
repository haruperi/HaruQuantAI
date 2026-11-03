/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.SQUtils
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks.random;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.SQUtils;
import java.math.BigDecimal;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RandomValueConfig {
    public static final Logger Log = LoggerFactory.getLogger((String)"RandomValueConfig");
    private boolean valid = true;
    private double val1;
    private double val2;
    private double step;
    private boolean isDouble;

    public RandomValueConfig(boolean bl) {
        this.valid = bl;
    }

    public RandomValueConfig(double d, double d2, double d3, boolean bl) {
        this.val1 = d;
        this.val2 = d2;
        this.step = d3;
        this.isDouble = bl;
    }

    public double generateRandomValue(IRandomGenerator iRandomGenerator, boolean bl) {
        return bl ? this.generateFromDoubleRange(iRandomGenerator) : this.generateFromIntRange(iRandomGenerator);
    }

    private double generateFromIntRange(IRandomGenerator iRandomGenerator) {
        int n;
        if (this.val1 == this.val2) {
            return (int)this.val1;
        }
        if ((this.val1 >= 0.0 || this.val2 >= 0.0) && this.val1 > this.val2) {
            return 2.147483647E9;
        }
        int n2 = (int)this.val2 - (int)this.val1;
        if (this.step == 0.0) {
            n = n2 / 100;
            if (n == 0) {
                n = 1;
            }
        } else {
            n = (int)this.step;
        }
        int n3 = n2 / n;
        int n4 = iRandomGenerator.nextInt(n3 + 1);
        int n5 = (int)this.val1 + n4 * n;
        return n5;
    }

    private double generateFromDoubleRange(IRandomGenerator iRandomGenerator) {
        double d;
        if (this.val1 == this.val2) {
            return this.val1;
        }
        if ((this.val1 >= 0.0 || this.val2 >= 0.0) && this.val1 > this.val2) {
            return Double.MAX_VALUE;
        }
        double d2 = this.val2 - this.val1;
        if (this.step == 0.0) {
            d = SQUtils.round2((double)(d2 / 100.0));
            if (d == 0.0) {
                d = SQUtils.round2((double)(d2 / 10.0));
            }
            if (d == 0.0) {
                d = SQUtils.round2((double)(d2 / 2.0));
            }
            if (d == 0.0) {
                return this.val1;
            }
        } else {
            d = this.step;
        }
        int n = (int)(d2 / d);
        int n2 = iRandomGenerator.nextInt(n + 1);
        double d3 = this.val1 + (double)n2 * d;
        return d3;
    }

    public boolean isValid() {
        return this.valid;
    }

    public static RandomValueConfig parseRandomValue(String string, boolean bl) {
        if (!string.contains(":")) {
            return RandomValueConfig.parseOldFormat(string, bl);
        }
        return RandomValueConfig.parseNewFormat(string, bl);
    }

    private static RandomValueConfig parseNewFormat(String string, boolean bl) {
        if (string.contains(":")) {
            String[] stringArray = string.split(":");
            if (stringArray == null) {
                return null;
            }
            try {
                if (stringArray.length == 2) {
                    double d = Double.parseDouble(stringArray[0]);
                    double d2 = Double.parseDouble(stringArray[1]);
                    return new RandomValueConfig(d, d2, 1.0, bl);
                }
                if (stringArray.length == 3) {
                    double d = Double.parseDouble(stringArray[0]);
                    double d3 = Double.parseDouble(stringArray[1]);
                    double d4 = Double.parseDouble(stringArray[2]);
                    return new RandomValueConfig(d, d3, d4, bl);
                }
                return null;
            }
            catch (NumberFormatException numberFormatException) {
                return null;
            }
        }
        try {
            double d = Double.parseDouble(string);
            return new RandomValueConfig(d, d, 0.0, bl);
        }
        catch (NumberFormatException numberFormatException) {
            return null;
        }
    }

    private static RandomValueConfig parseOldFormat(String string, boolean bl) {
        if (string.contains("-")) {
            String string2;
            String[] stringArray;
            String string3 = null;
            if (string.contains(";")) {
                stringArray = string.split(";");
                if (stringArray == null || stringArray.length != 2) {
                    return null;
                }
                string2 = stringArray[0];
                string3 = stringArray[1];
            } else {
                string2 = string;
            }
            stringArray = string2.split("-");
            if (stringArray == null || stringArray.length != 2) {
                return null;
            }
            try {
                double d = Double.parseDouble(stringArray[0]);
                double d2 = Double.parseDouble(stringArray[1]);
                double d3 = string3 == null ? 0.0 : Double.parseDouble(string3);
                return new RandomValueConfig(d, d2, d3, bl);
            }
            catch (NumberFormatException numberFormatException) {
                return null;
            }
        }
        try {
            double d = Double.parseDouble(string);
            return new RandomValueConfig(d, d, 0.0, bl);
        }
        catch (NumberFormatException numberFormatException) {
            return null;
        }
    }

    public int getDecimals(int n) {
        BigDecimal bigDecimal = BigDecimal.valueOf(this.val1);
        BigDecimal bigDecimal2 = BigDecimal.valueOf(this.val2);
        BigDecimal bigDecimal3 = BigDecimal.valueOf(this.step);
        int n2 = bigDecimal.scale();
        int n3 = bigDecimal2.scale();
        int n4 = bigDecimal3.scale();
        int n5 = n;
        if (n2 > n5) {
            n5 = n2;
        }
        if (n3 > n5) {
            n5 = n3;
        }
        if (n4 > n5) {
            n5 = n4;
        }
        if (n5 > 6) {
            n5 = 6;
        }
        return n5;
    }

    public boolean isInValidRange(double d) {
        return !(d < this.val1) && !(d > this.val2);
    }

    public void setMinMaxStepAttributes(Element element) {
        if (this.isDouble) {
            element.setAttribute("minValue", Double.toString(this.val1));
            element.setAttribute("maxValue", Double.toString(this.val2));
            element.setAttribute("step", Double.toString(this.step));
        } else {
            element.setAttribute("minValue", Integer.toString((int)this.val1));
            element.setAttribute("maxValue", Integer.toString((int)this.val2));
            element.setAttribute("step", Integer.toString((int)this.step));
        }
    }
}

