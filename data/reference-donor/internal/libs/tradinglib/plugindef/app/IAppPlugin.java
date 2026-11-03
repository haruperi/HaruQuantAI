/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.ISQPlugin
 */
package com.strategyquant.tradinglib.plugindef.app;

import com.strategyquant.pluginlib.ISQPlugin;

public interface IAppPlugin
extends ISQPlugin {
    public String getName();

    public String getContextPath();

    public String getAppCode();

    public String getTooltip();

    public String getProject();

    public String getDefaultTaskType();

    public String getDefaultTaskName();
}

