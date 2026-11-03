/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.websocket.channels.impl;

import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.websocket.channels.IProjectChannel;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BestResultsChannel
implements IProjectChannel {
    private static final Logger Log = LoggerFactory.getLogger(BestResultsChannel.class);

    @Override
    public Object getData(SQProject sQProject) {
        return sQProject.bestResults.print();
    }

    @Override
    public String getChannelName() {
        return "best-results-channel";
    }
}

