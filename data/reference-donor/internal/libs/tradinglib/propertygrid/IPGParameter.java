/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.settings.IXMLAble
 */
package com.strategyquant.tradinglib.propertygrid;

import com.strategyquant.lib.settings.IXMLAble;

public interface IPGParameter
extends IXMLAble {
    public String getName();

    public String getKey();

    public String getCategory();

    public String getEngine();

    public String getActivator();

    public void setActivator(String var1);

    public void setCategory(String var1);

    public void setEngine(String var1);

    public int getType();

    public String print();

    public void setValue(String var1);
}

