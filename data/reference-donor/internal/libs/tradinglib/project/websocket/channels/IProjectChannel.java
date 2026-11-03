/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.project.websocket.channels;

import com.strategyquant.tradinglib.project.SQProject;

public interface IProjectChannel {
    public Object getData(SQProject var1);

    public String getChannelName();
}

