/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(value=RetentionPolicy.RUNTIME)
public @interface Editor {
    public int type() default 0;

    public String formulaName() default "Null";

    public boolean allowVariables() default true;

    public String values() default "Null";
}

