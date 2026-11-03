/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.blocks.annotations;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(value=RetentionPolicy.RUNTIME)
public @interface DataSeriesChoice {
    public String key() default "ComputedFrom";

    public String name() default "Computed From";

    public String category() default "Default";

    public String help() default "Null";
}

