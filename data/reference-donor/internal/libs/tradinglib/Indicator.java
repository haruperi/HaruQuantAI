/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(value=RetentionPolicy.RUNTIME)
public @interface Indicator {
    public boolean oscillator() default false;

    public double middleValue() default 0.0;

    public double min() default -1000.0;

    public double max() default 1000.0;

    public double step() default 1.0;
}

