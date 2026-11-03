/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.pluginlib.ISQPlugin
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.crosscheck;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.pluginlib.ISQPlugin;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import java.io.Serializable;
import java.util.jar.JarFile;
import java.util.jar.JarOutputStream;
import org.jdom2.Element;

public interface ICrossCheck
extends ISQPlugin,
Serializable {
    public static final String CROSSCHECK_PREFIX = "CrossCheck_";
    public static final String CROSSCHECK_HIGHER_PRECISION_KEY = "CrossCheck_HigherPrecision";
    public static final String CROSSCHECK_WHAT_IF_KEY = "CrossCheck_WhatIf";
    public static final String CROSSCHECK_SEQUENTIAL_OPTIMIZATION_KEY = "CrossCheck_SequentialOptimization";

    public ICrossCheck clone(SettingsMap var1);

    public int getType();

    public String getName();

    public String getShortName();

    public SettingsMap getSettings();

    public String getSettingName();

    public String getDescription();

    public boolean runTest(ResultsGroup var1, int var2, double var3, GridJob var5, boolean var6, ILastEventListener var7, String var8) throws Exception;

    public void fixSettings(Element var1);

    public void readSettings(Element var1, TaskSettingsData var2) throws Exception;

    public int getDismissalReason();

    public String getDismissalMessage();

    public void setStopPauseEngine(StopPauseEngine var1);

    public void registerProgressListener(IBacktestProgressListener var1);

    public int getNumberOfSimulations();

    public boolean doesRetest();

    public boolean doesForEverySetup();

    public double getStatsValue(ResultsGroup var1, String var2, Element var3, Object ... var4) throws Exception;

    public String printSpecialValue(ResultsGroup var1, String var2, Element var3, Object ... var4) throws Exception;

    public String getColumnTitle(String var1, Element var2, Object ... var3);

    public String getColumnTitleTemplate();

    public void saveDataToFile(ResultsGroup var1, JarOutputStream var2) throws Exception;

    public void loadDataFromFile(ResultsGroup var1, JarFile var2) throws Exception;

    public ChartSetups getChartSetups(ChartSetup var1);

    public boolean doesCreateSubjobs();

    public boolean hasStatsValue(ResultsGroup var1, String var2, Element var3, Object ... var4) throws Exception;

    public String printSettings(Element var1) throws Exception;

    public int getBadStrategyReason();
}

