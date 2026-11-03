/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.blocks.annotations;

import com.strategyquant.tradinglib.ParameterSet;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(value=RetentionPolicy.RUNTIME)
public @interface ParameterSets {
    public ParameterSet[] value();
}

