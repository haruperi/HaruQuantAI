/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(value=RetentionPolicy.RUNTIME)
public @interface Parameter {
    public int defaultSeries() default 0;

    public int defaultChartIndex() default 0;

    public String defaultValue() default "Null";

    public String name() default "Null";

    public String category() default "Default";

    public double minValue() default 1.0;

    public double maxValue() default 10000.0;

    public double step() default 1.0;

    public boolean allowAny() default false;

    public boolean showIfDefault() default true;

    public String postfix() default "Null";

    public boolean isPeriod() default false;

    public double builderMinValue() default -9999999.0;

    public double builderMaxValue() default -9999999.0;

    public double builderStep() default -9999999.0;

    public int decimals() default 2;

    public String standsFor() default "Null";
}

