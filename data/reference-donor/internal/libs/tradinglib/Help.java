/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(value=RetentionPolicy.RUNTIME)
public @interface Help {
    public String value() default "Null";
}

