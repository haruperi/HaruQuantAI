/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.generator;

import org.jdom2.Element;

public interface IStrategyTemplate {
    public Element generate() throws Exception;

    public void setUseSameIdForLongShort(boolean var1);
}

