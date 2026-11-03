/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(value=RetentionPolicy.RUNTIME)
public @interface Formula {
    public String name() default "Null";

    public String formula() default "Null";

    public int order() default 100;

    public boolean noneValue() default false;

    public boolean priceLevel() default false;
}

