/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(value=RetentionPolicy.RUNTIME)
public @interface OppositeBlock {
    public String value() default "Null";

    public boolean oscillator() default false;

    public double middleValue() default 0.0;

    public String field() default "Null";
}

