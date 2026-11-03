/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.ISQPlugin
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.taskImpl;

import com.strategyquant.pluginlib.ISQPlugin;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectGlobalLog;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import org.jdom2.Element;

public interface ISQTask
extends ISQPlugin {
    public String getType();

    public String getName();

    public String getPluginFolderName();

    public String getCustomName();

    public String getTitle();

    public boolean isActive();

    public void setActive(boolean var1);

    public String[] getSettings();

    public TaskSettingsData getSettingsData();

    public void setCustomName(String var1);

    public void setTitle(String var1);

    public void setConfig(Element var1, boolean var2, boolean var3) throws Exception;

    public Element getConfig();

    public Element getDefaultConfig(String var1) throws Exception;

    public ISQTask clone(String var1, ProgressEngine var2) throws Exception;

    public void start() throws Exception;

    public void afterFinish();

    public void setTaskLogPrefix(String var1);

    public String getErrorsDescription();

    public void logTaskStarted(ProjectGlobalLog var1);

    public void logTaskFinished(ProjectGlobalLog var1);

    public void increaseNumberOfRuns();

    public int getNumberOfRuns();

    public int getIndex();

    public void setIndex(int var1);

    public void setConfigFileName(String var1);

    public String getTaskXMLFileName();

    public double getCustomValue(String var1);
}

