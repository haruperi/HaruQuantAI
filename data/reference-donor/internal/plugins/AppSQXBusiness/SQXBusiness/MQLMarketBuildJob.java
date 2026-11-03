/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.sqxbusiness.MQLMarketBuildResult
 *  com.strategyquant.lib.sqxbusiness.MQLMarketBuildSettings
 *  com.strategyquant.lib.sqxbusiness.MQLMarketBuilder
 *  com.strategyquant.lib.sqxbusiness.MQLMarketLoggable
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.App.impl.SQXBusiness;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.lib.sqxbusiness.MQLMarketBuildResult;
import com.strategyquant.lib.sqxbusiness.MQLMarketBuildSettings;
import com.strategyquant.lib.sqxbusiness.MQLMarketBuilder;
import com.strategyquant.lib.sqxbusiness.MQLMarketLoggable;
import com.strategyquant.plugin.App.impl.SQXBusiness.SQXBusinessBuildReporter;
import java.io.Serializable;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MQLMarketBuildJob
extends GridJob<MQLMarketBuildResult> {
    private static final Logger Log = LoggerFactory.getLogger((String)"MQLMarketBuildJob");
    private MQLMarketBuildSettings buildSettings;
    private MQLMarketBuilder builder;

    public MQLMarketBuildJob(String jobId, int flags, Map<String, Serializable> params) {
        super(jobId, flags, params);
        this.buildSettings = (MQLMarketBuildSettings)params.get("settings");
        this.builder = new MQLMarketBuilder(jobId);
    }

    public MQLMarketBuildResult call() throws Exception {
        SQXBusinessBuildReporter.printToLog(this.getJobId(), L.t((String)"Starting build...", (Object[])new Object[0]));
        SQXBusinessBuildReporter.setStatus(this.getJobId(), 1);
        return this.builder.build(this.buildSettings, (MQLMarketLoggable)SQXBusinessBuildReporter.get());
    }

    public void messageReceived(GridMessage message) {
        if (message.getMessageID() == 2) {
            SQXBusinessBuildReporter.printToLog(this.getJobId(), L.t((String)"Build paused", (Object[])new Object[0]));
            this.builder.pause();
        } else if (message.getMessageID() == 4) {
            SQXBusinessBuildReporter.printToLog(this.getJobId(), L.t((String)"Build stopped", (Object[])new Object[0]));
            this.builder.stop();
        } else if (message.getMessageID() == 3) {
            SQXBusinessBuildReporter.printToLog(this.getJobId(), L.t((String)"Build resumed", (Object[])new Object[0]));
            this.builder.resume();
        }
    }
}

