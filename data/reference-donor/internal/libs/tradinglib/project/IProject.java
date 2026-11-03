/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.ISQPlugin
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.pluginlib.ISQPlugin;
import com.strategyquant.tradinglib.ProjectRunInfo;
import com.strategyquant.tradinglib.project.Databanks;
import org.jdom2.Element;

public interface IProject
extends ISQPlugin {
    public Element setConfig() throws Exception;

    public Element getConfig() throws Exception;

    public Databanks getDatabanks();

    public String getName();

    public void start() throws Exception;

    public void stop();

    public void pause();

    public void resume() throws Exception;

    public int getRunningStatus();

    public void setRunningStatus(int var1);

    public int getRecentPos();

    public void setRecentPos(int var1);

    public void getTrackingInfo(ProjectRunInfo var1);
}

