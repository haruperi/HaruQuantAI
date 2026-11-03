/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(value=RetentionPolicy.RUNTIME)
public @interface BuildingBlock {
    public String name() default "Null";

    public String display() default "Null";

    public int returnType() default 1;

    public String mainIndicator() default "Null";
}

