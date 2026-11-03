/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.ISQPlugin
 *  org.eclipse.jetty.server.Handler
 */
package com.strategyquant.tradinglib.servlet;

import com.strategyquant.pluginlib.ISQPlugin;
import org.eclipse.jetty.server.Handler;

public interface IServletPlugin
extends ISQPlugin {
    public Handler getHandler();
}

