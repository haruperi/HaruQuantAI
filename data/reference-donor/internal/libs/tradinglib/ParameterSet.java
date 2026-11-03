/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.blocks.annotations.ParameterSets;
import java.lang.annotation.Repeatable;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(value=RetentionPolicy.RUNTIME)
@Repeatable(value=ParameterSets.class)
public @interface ParameterSet {
    public int weight() default 1;

    public String set() default "";
}

