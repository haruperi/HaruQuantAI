/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(value=RetentionPolicy.RUNTIME)
public @interface Output {
    public String name() default "Null";

    public String color() default "#FF0000";

    public boolean show() default true;

    public boolean showZeroValues() default true;

    public String chartType() default "line";
}

